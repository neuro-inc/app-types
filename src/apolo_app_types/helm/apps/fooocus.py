import typing as t

from yarl import URL

from apolo_app_types import (
    ContainerImage,
    CustomDeploymentInputs,
    FooocusAppInputs,
    Service,
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
    Env,
    MountPath,
    StorageMounts,
)


class FooocusChartValueProcessor(BaseChartValueProcessor[FooocusAppInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    async def _configure_env(
        self, data_volume: URL, outputs_volume: URL
    ) -> dict[str, str]:
        return {
            "CMDARGS": "--listen",
            "DATADIR": str(data_volume),
            "config_path": str(data_volume / "config.txt"),
            "config_example_path": str(
                data_volume / "config_modification_tutorial.txt"
            ),
            "path_checkpoints": str(data_volume / "models/checkpoints/"),
            "path_loras": str(
                data_volume / "models/loras/",
            ),
            "path_embeddings": str(data_volume / "models/embeddings/"),
            "path_vae_approx": str(data_volume / "models/vae_approx/"),
            "path_upscale_models": str(data_volume / "models/upscale_models/"),
            "path_inpaint": str(data_volume / "models/inpaint/"),
            "path_controlnet": str(data_volume / "models/controlnet/"),
            "path_clip_vision": str(data_volume / "models/clip_vision/"),
            "path_fooocus_expansion": str(
                data_volume / "models/prompt_expansion/fooocus_expansion/"
            ),
            "path_outputs": str(outputs_volume),
        }

    async def gen_extra_values(
        self,
        input_: FooocusAppInputs,
        app_name: str,
        namespace: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Foocus configuration.
        """

        base_app_storage_path = get_app_data_files_path_url(
            client=self.client, app_type=AppType.Fooocus, app_name=app_name
        )
        data_storage_path = base_app_storage_path / "data"
        data_container_dir = URL("/content/data")
        outputs_storage_path = base_app_storage_path / "app/outputs"
        outputs_container_dir = URL("/content/app/outputs")

        env = await self._configure_env(data_container_dir, outputs_container_dir)
        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=ContainerImage(
                repository="ghcr.io/neuro-inc/fooocus",
                tag="latest",
            ),
            ingress=input_.ingress,
            container=Container(env=[Env(name=k, value=v) for k, v in env.items()]),
            service=Service(port=7865),
            storage_mounts=StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_path=ApoloFilesPath(
                            path=str(data_storage_path),
                        ),
                        mount_path=MountPath(path=str(data_container_dir)),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                    ApoloFilesMount(
                        storage_path=ApoloFilesPath(
                            path=str(outputs_storage_path),
                        ),
                        mount_path=MountPath(path=str(outputs_container_dir)),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                ]
            ),
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
        )
        return {**custom_app_vals, "labels": {"application": "fooocus"}}
