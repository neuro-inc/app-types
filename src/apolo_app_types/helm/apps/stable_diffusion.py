import typing as t

from apolo_sdk import Preset

from apolo_app_types import StableDiffusionInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_extra_values,
    get_component_values,
    get_preset,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret


class StableDiffusionChartValueProcessor(
    BaseChartValueProcessor[StableDiffusionInputs]
):
    def _get_env_vars(
        self, input_: StableDiffusionInputs, preset: Preset, app_secrets_name: str
    ) -> dict[str, t.Any]:
        default_cmd_args = "--docs --cors-origins=*"
        if preset.nvidia_gpu and preset.nvidia_gpu.count > 0:
            commandline_args = "--use-cuda"
        elif preset.amd_gpu and preset.amd_gpu.count > 0:
            commandline_args = "--use-rocm"
        else:
            commandline_args = "--lowvram"
        return {
            "COMMANDLINE_ARGS": " ".join([default_cmd_args, commandline_args]),
            "HUGGING_FACE_HUB_TOKEN": serialize_optional_secret(
                input_.stable_diffusion.hugging_face_model.hf_token,
                secret_name=app_secrets_name,
            ),
        }

    def _get_image_repository(self, preset: Preset) -> str:
        if preset.nvidia_gpu:
            img_repo = "vladmandic/sdnext-cuda"
        elif preset.amd_gpu:
            img_repo = "disty0/sdnext-rocm:latest"
        else:
            img_repo = "disty0/sdnext-ipex:latest"

        return img_repo

    async def gen_extra_values(
        self,
        input_: StableDiffusionInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        preset_name = input_.preset.name
        generic_vals = await gen_extra_values(
            self.client,
            input_.preset,
            app_id,
            AppType.StableDiffusion,
            input_.ingress_http,
            None,
            namespace,
        )

        preset = get_preset(self.client, preset_name)

        component_vals = await get_component_values(preset, preset_name)
        api_vars = self._get_env_vars(input_, preset, app_secrets_name)
        img_repository = self._get_image_repository(preset)

        model_vals = {
            "model": {
                "modelHFName": input_.stable_diffusion.hugging_face_model.model_hf_name,
            }
        }
        return merge_list_of_dicts(
            [
                generic_vals,
                model_vals,
                {
                    "api": {
                        **component_vals,
                        "env": api_vars,
                        "image": {
                            "repository": img_repository,
                        },
                        "replicaCount": input_.stable_diffusion.replica_count,
                    },
                },
            ]
        )
