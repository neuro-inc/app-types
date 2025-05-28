import typing as t

from yarl import URL

from apolo_app_types import (
    ContainerImage,
    CustomDeploymentInputs,
)
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.protocols.common import Container, Env, StorageMounts
from apolo_app_types.protocols.common.health_check import (
    HealthCheck,
    HealthCheckProbesConfig,
    HTTPHealthCheckConfig,
)
from apolo_app_types.protocols.common.ingress import IngressHttp
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    ApoloMountModes,
    MountPath,
)
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from apolo_app_types.protocols.jupyter import (
    _JUPYTER_DEFAULTS,
    JupyterAppInputs,
)


class JupyterChartValueProcessor(BaseChartValueProcessor[JupyterAppInputs]):
    _default_code_mount_path: URL = URL("/root/notebooks")
    _jupyter_port: int = 8888

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    def _get_default_code_storage_mount(self) -> ApoloFilesMount:
        return ApoloFilesMount(
            storage_uri=ApoloFilesPath(path=_JUPYTER_DEFAULTS["storage"]),
            mount_path=MountPath(path=_JUPYTER_DEFAULTS["mount"]),
            mode=ApoloMountMode(mode=ApoloMountModes.RW),
        )

    async def gen_extra_values(
        self,
        input_: JupyterAppInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Jupyter configuration.
        """

        code_storage_mount = (
            input_.jupyter_specific.override_code_storage_mount
            or self._get_default_code_storage_mount()
        )
        storage_mounts = input_.extra_storage_mounts or StorageMounts(mounts=[])
        storage_mounts.mounts.append(code_storage_mount)

        jupyter_args = (
            f"--ServerApp.root_dir={code_storage_mount.mount_path.path} "
            "--ServerApp.token= "
            "--ServerApp.password= "
            f"--ServerApp.port={self._jupyter_port}"
            "--ServerApp.ip=0.0.0.0 "
            f"--ServerApp.default_url={code_storage_mount.mount_path.path}/README.ipynb)"
        )

        env_vars = []
        if input_.mlflow_integration and input_.mlflow_integration.internal_url:
            env_vars.append(
                Env(
                    name="MLFLOW_TRACKING_URI",
                    value=input_.mlflow_integration.internal_url.complete_url,
                )
            )

        image, tag = input_.jupyter_specific.container_image.value.split(":")
        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository=image,
                tag=tag,
            ),
            container=Container(
                command=[
                    "bash",
                    "-c",
                    (
                        f"(mkdir -p {code_storage_mount.mount_path.path}) && "
                        "(rsync -a --ignore-existing "
                        f"{code_storage_mount.mount_path.path}/README.ipynb "
                        f"{code_storage_mount.mount_path.path}) && "
                        f"(start-notebook.py {jupyter_args} "
                    ),
                ],
                env=env_vars,
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress_http=IngressHttp(auth=input_.networking.http_auth),
                ports=[
                    Port(name="http", port=self._jupyter_port),
                ],
            ),
            storage_mounts=storage_mounts,
            health_checks=HealthCheckProbesConfig(
                liveness=HealthCheck(
                    enabled=True,
                    initial_delay=30,
                    period_seconds=5,
                    timeout=5,
                    failure_threshold=20,
                    health_check_config=HTTPHealthCheckConfig(
                        path="/",
                        port=self._jupyter_port,
                    ),
                ),
                readiness=HealthCheck(
                    enabled=True,
                    initial_delay=30,
                    period_seconds=5,
                    timeout=5,
                    failure_threshold=20,
                    health_check_config=HTTPHealthCheckConfig(
                        path="/",
                        port=self._jupyter_port,
                    ),
                ),
            ),
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
        )
        return {**custom_app_vals, "labels": {"application": "jupyter"}}
