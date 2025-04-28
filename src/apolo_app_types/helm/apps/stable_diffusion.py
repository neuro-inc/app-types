import typing as t

from apolo_sdk import Preset

from apolo_app_types import StableDiffusionInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_extra_values,
    get_component_values,
    get_preset,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts


class StableDiffusionChartValueProcessor(
    BaseChartValueProcessor[StableDiffusionInputs]
):
    def _get_env_vars(self, preset: Preset) -> dict[str, t.Any]:
        default_cmd_args = "--docs --cors-origins=*"
        if preset.nvidia_gpu:
            commandline_args = "--use-cuda"
        elif preset.amd_gpu:
            commandline_args = "--use-rocm"
        else:
            commandline_args = "--lowvram"

        return {"COMMANDLINE_ARGS": " ".join([default_cmd_args, commandline_args])}

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
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        preset_name = input_.preset.name
        generic_vals = await gen_extra_values(
            self.client, input_.preset, input_.ingress_http, None, namespace
        )

        preset = get_preset(self.client, preset_name)

        component_vals = get_component_values(preset, preset_name)
        api_vars = self._get_env_vars(preset)
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
