import typing as t

from apolo_app_types import (
    ContainerImage,
    CustomDeploymentInputs,
)
from apolo_app_types.app_types import AppType
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
    CustomImage,
    DefaultContainer,
    JupyterAppInputs,
    JupyterImage,
)


class JupyterChartValueProcessor(BaseChartValueProcessor[JupyterAppInputs]):
    _jupyter_port: int = 8888

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    def _get_default_code_storage_mount(
        self, input_: JupyterAppInputs
    ) -> ApoloFilesMount:
        container = input_.jupyter_specific.container_settings
        mount_path = _JUPYTER_DEFAULTS["mount"]
        if (
            isinstance(container, DefaultContainer)
            and container.container_image != JupyterImage.APOLO_BASE_IMAGE
        ):
            mount_path = "/home/jovyan"

        return ApoloFilesMount(
            storage_uri=ApoloFilesPath(path=_JUPYTER_DEFAULTS["storage"]),
            mount_path=MountPath(path=mount_path),
            mode=ApoloMountMode(mode=ApoloMountModes.RW),
        )

    def get_default_image_args(
        self, image: JupyterImage, code_storage_mount: ApoloFilesMount
    ) -> tuple[t.Sequence[str] | None, t.Sequence[str] | None]:
        match image:
            case JupyterImage.APOLO_BASE_IMAGE:
                jupyter_args = (
                    "--no-browser "
                    "--ip=0.0.0.0 "
                    f"--port {self._jupyter_port} "
                    "--allow-root "
                    "--NotebookApp.token= "
                    f"--notebook-dir={code_storage_mount.mount_path.path} "
                    f"--NotebookApp.default_url={code_storage_mount.mount_path.path}/README.ipynb)"
                )
                command = (
                    "bash",
                    "-c",
                    (
                        f"(mkdir -p {code_storage_mount.mount_path.path}) && "
                        "(rsync -a --ignore-existing "
                        "/var/notebooks/README.ipynb "
                        f"{code_storage_mount.mount_path.path}) && "
                        f"(jupyter lab {jupyter_args} "
                    ),
                )
                return command, None
            # case JupyterImage.BASE_NOTEBOOK | JupyterImage.PYTORCH_NOTEBOOK:
            #     return None, (
            #         "start-notebook.py",
            #         f"--ServerApp.root_dir={code_storage_mount.mount_path.path}",
            #         "--IdentityProvider.auth_enabled=false",
            #         "--PasswordIdentityProvider.password_required=false",
            #         f"--ServerApp.port={self._jupyter_port}",
            #         "--ServerApp.ip=0.0.0.0",
            #         f"--ServerApp.default_url={code_storage_mount.mount_path.path}",
            #     )
            # case _:
            #     err = f"Unsupported Jupyter image: {image}"
            #     raise ValueError(err)

    def get_container(
        self, input_: JupyterAppInputs
    ) -> tuple[ContainerImage, Container]:
        code_storage_mount = self.get_code_storage_mount(input_)
        env_vars = []

        if input_.mlflow_integration and input_.mlflow_integration.internal_url:
            env_vars.append(
                Env(
                    name="MLFLOW_TRACKING_URI",
                    value=input_.mlflow_integration.internal_url.complete_url,
                )
            )

        match container_settings := input_.jupyter_specific.container_settings:
            case DefaultContainer():
                image, tag = container_settings.container_image.value.split(":")
                cmd, args = self.get_default_image_args(
                    image=container_settings.container_image,
                    code_storage_mount=code_storage_mount,
                )
                return ContainerImage(
                    repository=image,
                    tag=tag,
                ), Container(
                    command=cmd,
                    args=args,
                    env=env_vars,
                )
            case CustomImage():
                container = container_settings.container_config
                container.env.extend(env_vars)
                return container_settings.container_image, container
            case _:
                err = "Unsupported container configuration type."
                raise ValueError(err)

    def get_code_storage_mount(self, input_: JupyterAppInputs) -> ApoloFilesMount:
        """
        Get the code storage mount for Jupyter.
        If the user has overridden the default, use that; otherwise, return the default.
        """
        return (
            input_.jupyter_specific.override_code_storage_mount
            or self._get_default_code_storage_mount(input_)
        )

    async def gen_extra_values(
        self,
        input_: JupyterAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Jupyter configuration.
        """

        code_storage_mount = self.get_code_storage_mount(input_)
        storage_mounts = input_.extra_storage_mounts or StorageMounts(mounts=[])
        storage_mounts.mounts.append(code_storage_mount)

        image, container = self.get_container(input_)
        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=image,
            container=container,
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
            app_id=app_id,
            app_secrets_name=app_secrets_name,
            app_type=AppType.Jupyter,
        )
        return {**custom_app_vals, "labels": {"application": "jupyter"}}
