import typing as t

from apolo_app_types import StableDiffusionInputs
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_sdk import Preset

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    get_component_values,
    get_preset,
    gen_extra_values
)
from apolo_app_types.helm.apps.ingress import (
    _generate_ingress_config,
    get_ingress_values,
)


class StableDiffusionChartValueProcessor(BaseChartValueProcessor[StableDiffusionInputs]):

    def _get_env_vars(self, preset: Preset) -> dict[str, t.Any]:
        basic_cmd_args = (
            "--api --no-download-sd-model --cors-allow-origins=* "
            "--skip-version-check --skip-torch-cuda-test "
            "--allow-code --enable-insecure-extension-access"
        )

        if any([preset.nvidia_gpu, preset.amd_gpu]):
            commandline_args = basic_cmd_args
        else:
            commandline_args = (
                f"{basic_cmd_args} "
                f"--lowvram --use-cpu all --no-half --precision full"
            )

        return {"COMMANDLINE_ARGS": commandline_args}

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

        stablestudio = {}
        if input_.stable_diffusion.stablestudio and input_.stable_diffusion.stablestudio.enabled:
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

        return merge_list_of_dicts([generic_vals, stablestudio, {
                    "api": {
                        **ingress_api,
                        **component_vals,
                        "env": api_vars,
                    },
                },
            ]
        )
