import typing as t

from apolo_app_types import CustomDeploymentInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
)
from apolo_app_types.helm.utils.images import get_apolo_registry_secrets_value


class CustomDeploymentChartValueProcessor(
    BaseChartValueProcessor[CustomDeploymentInputs]
):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    def _configure_storage_annotations(
        self, input_: CustomDeploymentInputs
    ) -> dict[str, str]:
        """
        If 'storage_mounts' is non-empty, generate the appropriate JSON annotation
        so that Apolo's storage injection can mount them.
        """
        if not input_.storage_mounts:
            return {}
        return append_apolo_storage_integration_annotations(
            {}, input_.storage_mounts.mounts
        )

    def _configure_storage_labels(
        self, input_: CustomDeploymentInputs
    ) -> dict[str, str]:
        """
        If 'storage_mounts' is non-empty, add a label to indicate
        that storage injection is needed.
        """
        if not input_.storage_mounts:
            return {}
        return gen_apolo_storage_integration_labels(inject_storage=True)

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

        storage_annotations = self._configure_storage_annotations(input_)
        if storage_annotations:
            values["podAnnotations"] = storage_annotations

        storage_labels = self._configure_storage_labels(input_)
        if storage_labels:
            values["podLabels"] = storage_labels

        if input_.image.repository.startswith("images:"):
            values["dockerconfigjson"] = str(
                await get_apolo_registry_secrets_value(client=self.client)
            )
        elif input_.image.dockerconfigjson:
            values["dockerconfigjson"] = input_.image.dockerconfigjson.filecontents
        return values
