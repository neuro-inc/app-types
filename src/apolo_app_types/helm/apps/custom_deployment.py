import typing as t

from apolo_app_types import CustomDeploymentInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
)


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
        if not input_.custom_deployment.storage_mounts:
            return {}
        return append_apolo_storage_integration_annotations(
            {}, input_.custom_deployment.storage_mounts
        )

    def _configure_storage_labels(
        self, input_: CustomDeploymentInputs
    ) -> dict[str, str]:
        """
        If 'storage_mounts' is non-empty, add a label to indicate
        that storage injection is needed.
        """
        if not input_.custom_deployment.storage_mounts:
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
            preset_type=input_.custom_deployment.preset,
            namespace=namespace,
            ingress=input_.custom_deployment.ingress,
        )
        values: dict[str, t.Any] = {
            "image": {
                "repository": input_.custom_deployment.image.repository,
                "tag": input_.custom_deployment.image.tag or "latest",
            },
            **extra_values,
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

        if input_.custom_deployment.name_override:
            values["nameOverride"] = input_.custom_deployment.name_override

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

        storage_annotations = self._configure_storage_annotations(input_)
        if storage_annotations:
            values["podAnnotations"] = storage_annotations

        storage_labels = self._configure_storage_labels(input_)
        if storage_labels:
            values["podExtraLabels"] = storage_labels

        if input_.dockerconfigjson:
            values["dockerconfigjson"] = input_.dockerconfigjson.filecontents
        return values
