import typing as t

import apolo_sdk
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.custom_deployment import CustomDeploymentModel, Container, Env
from apolo_sdk import Preset

from apolo_app_types import FooocusAppInputs, CustomDeploymentInputs, ContainerImage
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
    get_preset,
)
from apolo_app_types.helm.apps.custom_deployment import CustomDeploymentChartValueProcessor
from apolo_app_types.helm.utils.storage import get_app_data_storage_path
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common import (
    ApoloMountMode,
    ApoloStorageMount,
    MountPath,
)
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.llm import LLMModel


class FooocusChartValueProcessor(BaseChartValueProcessor[FooocusAppInputs]):
    app_image: str = "ghcr.io/neuro-inc/fooocus:latest"
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(*args, **kwargs)

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    async def _configure_env(self, app_name: str) -> dict[str, str]:
        base_app_storage_path = get_app_data_storage_path(
            client=self.client, app_type=AppType.Fooocus, app_name=app_name
        )
        data_volume = base_app_storage_path / "data/content/data"
        outputs_volume = base_app_storage_path /"app/outputs/content/app/outputs"
        return {
            "CMDARGS": "--listen",
            "DATADIR": str(data_volume),
            "config_path": str(data_volume / "config.txt"),
            "config_example_path": str(
                data_volume / "config_modification_tutorial.txt"
            ),
            "path_checkpoints": str(
                data_volume / "models/checkpoints/"
            ),
            "path_loras": str(data_volume / "models/loras/",),
            "path_embeddings": str(data_volume / "models/embeddings/"),
            "path_vae_approx": str(data_volume / "models/vae_approx/"),
            "path_upscale_models": str(
                data_volume / "models/upscale_models/"
            ),
            "path_inpaint":    str(data_volume / "models/inpaint/"),
            "path_controlnet": str(data_volume / "models/controlnet/"),
            "path_clip_vision": str(
                data_volume / "models/clip_vision/"
            ),
            "path_fooocus_expansion": str(
                data_volume /
                "/models/prompt_expansion/fooocus_expansion/"
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
        values = await gen_extra_values(
            self.client,
            input_.preset,
            input_.ingress,
            namespace,
        )

        env = await self._configure_env(app_name)
        custom_deployment = CustomDeploymentInputs(
            custom_deployment=CustomDeploymentModel(
                preset=input_.preset,
                image=ContainerImage(
                    repository="ghcr.io/neuro-inc/fooocus",
                    tag="latest",
                ),
                container=Container(
                    env=[
                        Env(name=k, value=v) for k, v in env.items()
                    ]
                )
            ),

        )

        return await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
            *args,
            **kwargs,
        )
