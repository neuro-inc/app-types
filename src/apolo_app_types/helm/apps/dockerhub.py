import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.protocols.dockerhub import (
    DockerHubInputs,
    DockerHubModel,
)


class DockerHubModelChartValueProcessor(BaseChartValueProcessor[DockerHubInputs]):
    _DOCKERHUB_API_URL = "https://hub.docker.com"

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    async def gen_extra_values(
        self,
        input_: DockerHubInputs,
        app_name: str,
        namespace: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for LLM configuration.
        Incorporates:
          - Existing autoscaling logic
          - GPU detection for parallel settings
        """
        return {
            "job": {
                "args": {
                    "org": self.client.config.org_name,
                    "namespace": namespace,
                    "project": self.client.config.project_name,
                    "user": self.client.username,
                    "registry_name": "DockerHub",
                    "registry_provider_host": DockerHubModel.registry_url,
                    "registry_api_url": self._DOCKERHUB_API_URL,
                    "registry_user": input_.username,
                    "registry_secret": input_.password,
                }
            }
        }
