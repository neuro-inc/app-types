import typing as t

from apolo_sdk import Preset

from apolo_app_types import StableDiffusionInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_extra_values,
    get_component_values,
    get_preset,
)
from apolo_app_types.helm.apps.ingress import (
    _generate_ingress_config,
    get_ingress_values,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts


class StableDiffusionChartValueProcessor(
    BaseChartValueProcessor[StableDiffusionInputs]
):
    def _get_env_vars(self, preset: Preset) -> dict[str, t.Any]:
        default_cmd_args = "--docs"
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
            self.client, input_.preset, input_.ingress, namespace
        )

        preset = get_preset(self.client, preset_name)

        ingress_api = await get_ingress_values(
            self.client,
            input_.ingress,
            namespace,
        )

        component_vals = get_component_values(preset, preset_name)
        api_vars = self._get_env_vars(preset)
        img_repository = self._get_image_repository(preset)
        stablestudio = {}
        if (
            input_.stable_diffusion.stablestudio
            and input_.stable_diffusion.stablestudio.enabled
        ):
            stable_studio_domain_suffix = "-ss"
            stable_studio_ingress = await _generate_ingress_config(
                self.client, namespace, stable_studio_domain_suffix
            )
            ss_preset_name = input_.stable_diffusion.stablestudio.preset.name
            if not ss_preset_name:
                msg = "Missing required key preset_name for stablestudio in helm args."
                raise Exception(msg)
            ss_preset = get_preset(self.client, ss_preset_name)
            stablestudio_component = get_component_values(ss_preset, ss_preset_name)
            stablestudio["ingress"] = stable_studio_ingress
            stablestudio.update(stablestudio_component)
        model_vals = {
            "model": {
                "modelHFName": input_.stable_diffusion.hugging_face_model.modelHFName,
                "modelFiles": input_.stable_diffusion.hugging_face_model.modelFiles,
            }
        }
        return merge_list_of_dicts(
            [
                generic_vals,
                stablestudio,
                model_vals,
                {
                    "api": {
                        **ingress_api,
                        **component_vals,
                        "env": api_vars,
                        "image": {
                            "repository": img_repository,
                        },
                    },
                },
            ]
        )
