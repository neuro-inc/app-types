import typing as t
from datetime import datetime

from apolo_app_types import CustomDeploymentInputs, DockerConfigModel
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
)
from apolo_app_types.helm.utils.images import (
    get_apolo_registry_secrets_value,
    get_image_docker_url,
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
        return gen_apolo_storage_integration_labels(
            client=self.client, inject_storage=True
        )

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
            ingress=input_.networking.ingress,
            port_configurations=input_.networking.ports,
        )
        image_docker_url = await get_image_docker_url(
            client=self.client,
            image=input_.image.repository,
            tag=input_.image.tag or "latest",
        )
        image, tag = image_docker_url.rsplit(":", 1)
        values: dict[str, t.Any] = {
            "image": {
                "repository": image,
                "tag": tag,
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
        if input_.networking and input_.networking.service_enabled:
            values["service"] = {
                "enabled": True,
                "ports": [
                    {
                        "name": _.name,
                        "containerPort": _.port,
                    }
                    for _ in input_.networking.ports
                ],
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

        dockerconfig: DockerConfigModel | None = input_.image.dockerconfigjson

        if input_.image.repository.startswith("image:"):
            sa_suffix = (
                input_.name_override.name
                if input_.name_override
                else datetime.now().strftime("%Y%m%d%H%M%S")
            )
            sa_name = f"custom-deployment-{sa_suffix}"
            dockerconfig = await get_apolo_registry_secrets_value(
                client=self.client, sa_name=sa_name
            )

        if dockerconfig:
            values["dockerconfigjson"] = dockerconfig.filecontents
        return values
