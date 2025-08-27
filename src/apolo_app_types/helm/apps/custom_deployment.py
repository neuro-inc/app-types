import typing as t

from apolo_app_types import CustomDeploymentInputs, DockerConfigModel
from apolo_app_types.app_types import AppType
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
from apolo_app_types.helm.utils.pods import get_custom_deployment_health_check_values


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
            {}, input_.storage_mounts.mounts, client=self.client
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
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Custom Deployment.
        """
        app_type = kwargs.get("app_type", AppType.CustomDeployment)
        extra_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            namespace=namespace,
            ingress_http=input_.networking.ingress_http,
            ingress_grpc=None,
            port_configurations=input_.networking.ports,
            app_id=app_id,
            app_type=app_type,
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
                "pullPolicy": input_.image.pull_policy.value,
            },
            **extra_values,
        }

        if input_.container:
            values["container"] = {
                "command": input_.container.command,
                "args": input_.container.args,
                "env": [
                    {"name": env.name, "value": env.deserialize_value(app_secrets_name)}
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
                ]
                if input_.networking.ports
                else [{"name": "http", "containerPort": 80}],
            }

        if input_.autoscaling:
            values["autoscaling"] = {
                "enabled": True,
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
            sa_name = f"custom-deployment-{app_name}"
            dockerconfig = await get_apolo_registry_secrets_value(
                client=self.client, sa_name=sa_name
            )

        if dockerconfig:
            values["dockerconfigjson"] = dockerconfig.filecontents

        health_checks = get_custom_deployment_health_check_values(input_.health_checks)
        values |= health_checks

        configmap_name = "app-configmap"
        if input_.config_map:
            values["configMap"] = {
                "enabled": True,
                "name": configmap_name,
                "data": {item.key: item.value for item in input_.config_map.data},
            }
            volume = {
                "name": configmap_name,
                "configMap": {
                    "name": configmap_name,
                },
            }
            volume_mount = {
                "name": configmap_name,
                "mountPath": input_.config_map.mount_path.path,
            }
            values.setdefault("volumes", []).append(volume)
            values.setdefault("volumeMounts", []).append(volume_mount)

        return values
