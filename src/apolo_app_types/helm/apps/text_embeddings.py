import typing as t

from apolo_app_types import (
    CustomDeploymentInputs,
)
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.custom_deployment import NetworkingConfig
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs


class TextEmbeddingsChartValueProcessor(
    BaseChartValueProcessor[TextEmbeddingsInferenceAppInputs]
):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    async def gen_extra_values(
        self,
        input_: TextEmbeddingsInferenceAppInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for TEI configuration.
        """

        custom_deployment = CustomDeploymentInputs(
            preset=input_.preset,
            image=input_.container_image,
            networking=NetworkingConfig(
                service_enabled=True,
                ingress=input_.ingress,
                ports=[
                    Port(name="http", port=3000),
                ],
            ),
        )

        custom_app_vals = await self.custom_dep_val_processor.gen_extra_values(
            input_=custom_deployment,
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
        )
        return {**custom_app_vals, "labels": {"application": "tei"}}
