import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs


class TextEmbeddingsChartValueProcessor(
    BaseChartValueProcessor[TextEmbeddingsInferenceAppInputs]
):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    def _configure_model_download(
        self, input_: TextEmbeddingsInferenceAppInputs
    ) -> dict[str, t.Any]:
        return {
            "modelHFName": input_.model.model_hf_name,
        }

    def _get_image_params(
        self, input_: TextEmbeddingsInferenceAppInputs
    ) -> dict[str, t.Any]:
        return {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "1.7",
        }

    def _configure_env(
        self, tei: TextEmbeddingsInferenceAppInputs, app_secrets_name: str
    ) -> dict[str, t.Any]:
        return {
            "HUGGING_FACE_HUB_TOKEN": serialize_optional_secret(
                tei.model.hf_token, secret_name=app_secrets_name
            )
        }

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
        values = await gen_extra_values(
            self.client,
            input_.preset,
            input_.ingress_http,
            None,
            namespace,
        )
        model = self._configure_model_download(input_)
        image = self._get_image_params(input_)
        env = self._configure_env(input_, app_secrets_name)
        return merge_list_of_dicts(
            [
                {
                    "model": model,
                    "image": image,
                    "env": env,
                },
                values,
            ]
        )
