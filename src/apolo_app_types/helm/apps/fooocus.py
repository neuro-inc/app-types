import typing as t

from apolo_app_types.protocols.custom_deployment import CustomDeploymentModel
from apolo_sdk import Preset

from apolo_app_types import FooocusAppInputs, CustomDeploymentInputs, ContainerImage
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
    get_preset,
)
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

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    async def _configure_env(self):
        base_app_storage = URL(f"storage:.apps_data/{AppType.Fooocus}/{app_name}")
        data_volume = apolo_sdk.Volume(base_app_storage / "data", "/content/data")
        outputs_volume = apolo_sdk.Volume(
            base_app_storage / "app/outputs", "/content/app/outputs"
        )
        return {
            "CMDARGS": "--listen",
            "DATADIR": data_volume.container_path,
            "config_path": f"{data_volume.container_path}/config.txt",
            "config_example_path": (
                f"{data_volume.container_path}/config_modification_tutorial.txt"
            ),
            "path_checkpoints": (
                f"{data_volume.container_path}/models/checkpoints/"
            ),
            "path_loras": f"{data_volume.container_path}/models/loras/",
            "path_embeddings": f"{data_volume.container_path}/models/embeddings/",
            "path_vae_approx": f"{data_volume.container_path}/models/vae_approx/",
            "path_upscale_models": (
                f"{data_volume.container_path}/models/upscale_models/"
            ),
            "path_inpaint": f"{data_volume.container_path}/models/inpaint/",
            "path_controlnet": f"{data_volume.container_path}/models/controlnet/",
            "path_clip_vision": (
                f"{data_volume.container_path}/models/clip_vision/"
            ),
            "path_fooocus_expansion": (
                f"{data_volume.container_path}"
                "/models/prompt_expansion/fooocus_expansion/"
            ),
            "path_outputs": f"{outputs_volume.container_path}/",
        }

    async def gen_extra_values(
        self,
        input_: FooocusAppInputs,
        app_name: str,
        namespace: str,
        *_: t.Any,
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
        custom_deployment = CustomDeploymentInputs(
            custom_deployment=CustomDeploymentModel(
                preset=input_.preset,
                image=ContainerImage(
                    repository="ghcr.io/neuro-inc/fooocus",
                    tag="latest",
                )
            ),
        )
        env = await self._configure_env()
        return merge_list_of_dicts(
            [
                {"env": env},
            ]
        )

        secret_envs = {}
        if app_inputs.huggingface_token_secret:
            secret_envs["HUGGINGFACE_TOKEN"] = app_inputs.huggingface_token_secret

        if secret_envs:
            job_parameters["secret_env"] = secret_envs

        return job_parameters