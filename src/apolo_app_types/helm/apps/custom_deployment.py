import typing as t

from apolo_app_types import CustomDeploymentInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor


class CustomDeploymentChartValueProcessor(
    BaseChartValueProcessor[CustomDeploymentInputs]
):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def gen_extra_values(
        self,
        input_: CustomDeploymentInputs,
        app_name: str,
        namespace: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for LLM configuration.
        """
        # preset_name = input_.preset_name
        # preset: Preset = get_preset(self.client, preset_name)
        return {
            "image": {
                "repository": input_.image.repository,  # type: ignore
                "tag": input_.image.tag or "latest",  # type: ignore
            }
        }
