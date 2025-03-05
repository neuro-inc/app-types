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
        values: dict[str, t.Any] = {
            "image": {
                "repository": input_.custom_deployment.image.repository,
                "tag": input_.custom_deployment.image.tag or "latest",
            }
        }
        if input_.custom_deployment.container:
            values["container"] = {
                "command": input_.custom_deployment.container.command,
                "args": input_.custom_deployment.container.args,
                "env": [
                    {"name": env.name, "value": env.value}
                    for env in input_.custom_deployment.container.env
                ],
            }
        if (
            input_.custom_deployment.service
            and input_.custom_deployment.service.enabled
        ):
            values["service"] = {
                "enabled": True,
                "port": input_.custom_deployment.service.port,
            }

        if (
            input_.custom_deployment.autoscaling
            and input_.custom_deployment.autoscaling.enabled
        ):
            values["autoscaling"] = {
                "enabled": True,
                "type": input_.custom_deployment.autoscaling.type,
                "min_replicas": input_.custom_deployment.autoscaling.min_replicas,
                "max_replicas": input_.custom_deployment.autoscaling.max_replicas,
                "target_cpu_utilization_percentage": (
                    input_.custom_deployment.autoscaling.target_cpu_utilization_percentage
                ),
                "target_memory_utilization_percentage": (
                    input_.custom_deployment.autoscaling.target_memory_utilization_percentage
                ),
            }
        return values
