import typing as t

from apolo_app_types import CustomDeploymentInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_extra_values,
)


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
        Generate extra Helm values for Custom Deployment.
        """
        extra_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            namespace=namespace,
            ingress=input_.ingress,
        )
        values: dict[str, t.Any] = {
            "image": {
                "repository": input_.image.repository,
                "tag": input_.image.tag or "latest",
            },
            **extra_values,
        }

        if input_.container:
            values["container"] = {
                "command": input_.container.command,
                "args": input_.container.args,
                "env": [
                    {"name": env.name, "value": env.value}
                    for env in input_.container.env
                ],
            }
        if input_.service and input_.service.enabled:
            values["service"] = {
                "enabled": True,
                "port": input_.service.port,
            }

        if input_.name_override:
            values["nameOverride"] = input_.name_override.name

        if input_.autoscaling and input_.autoscaling.enabled:
            values["autoscaling"] = {
                "enabled": True,
                "type": input_.autoscaling.type,
                "min_replicas": input_.autoscaling.min_replicas,
                "max_replicas": input_.autoscaling.max_replicas,
                "target_cpu_utilization_percentage": (
                    input_.autoscaling.target_cpu_utilization_percentage
                ),
                "target_memory_utilization_percentage": (
                    input_.autoscaling.target_memory_utilization_percentage
                ),
            }

        if input_.image.dockerconfigjson:
            values["dockerconfigjson"] = input_.image.dockerconfigjson.filecontents
        return values
