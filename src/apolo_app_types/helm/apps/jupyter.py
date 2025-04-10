import typing as t

from yarl import URL

from apolo_app_types import (
    ContainerImage,
    CustomDeploymentInputs,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.helm.utils.storage import get_app_data_files_path_url
from apolo_app_types.protocols.common import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    Container,
    MountPath,
    StorageMounts,
)
from apolo_app_types.protocols.common.ingress import Ingress
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from apolo_app_types.protocols.jupyter import JupyterAppInputs, JupyterTypes


class JupyterChartValueProcessor(BaseChartValueProcessor[JupyterAppInputs]):
    _default_code_mount_path: URL = URL("/root/notebooks")
    _jupyter_port: int = 8888

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_values(
        self,
        input_: JupyterAppInputs,
        app_name: str,
        namespace: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Foocus configuration.
        """

        code_storage_mount = input_.jupyter_specific.code_storage_mount
        if not code_storage_mount:
            base_app_storage_path = get_app_data_files_path_url(
                client=self.client, app_type=AppType.Jupyter, app_name=app_name
            )
            code_storage_mount = ApoloFilesMount(
                storage_uri=ApoloFilesPath(
                    path=str(base_app_storage_path / "code"),
                ),
                mount_path=MountPath(path=str(self._default_code_mount_path)),
                mode=ApoloMountMode(mode="rw"),
            )
        storage_mounts = input_.jupyter_specific.extra_storage_mounts or StorageMounts(
            mounts=[]
        )
        storage_mounts.mounts.append(code_storage_mount)

        jupyter_args = (
            "--no-browser "
            "--ip=0.0.0.0 "
            f"--port {self._jupyter_port} "
            "--allow-root "
            "--NotebookApp.token= "
            f"--notebook-dir={code_storage_mount.mount_path} "
            # "--NotebookApp.shutdown_no_activity_timeout=7200 "
            # "--MappingKernelManager.cull_idle_timeout=7200 "
            # "--MappingKernelManager.cull_connected=True"
            # see https://apolocloud.slack.com/archives/C07KJJBE2S2/p1741960663342579
        )
        cmd = "lab"
        if input_.jupyter_specific.jupyter_type == JupyterTypes.NOTEBOOK:
            cmd = "notebook"

        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/neuro-inc/base",
                tag="pipelines",
            ),
            container=Container(
                command=[
                    (
                        f'bash -c "(rsync -a --ignore-existing '
                        "/var/notebooks/README.ipynb "
                        f"{code_storage_mount.mount_path}) && "
                        f"(jupyter {cmd} {jupyter_args} "
                        f'--NotebookApp.default_url={code_storage_mount.mount_path}/README.ipynb)"'
                    )
                ]
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ingress=Ingress(enabled=True),
                ports=[
                    Port(name="http", port=self._jupyter_port),
                ],
            ),
            storage_mounts=storage_mounts,
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
        )
        return {**custom_app_vals, "labels": {"application": "jupyter"}}
