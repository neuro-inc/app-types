import typing as t

from apolo_app_types import HuggingFaceModel
from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.openai_compat import OpenAICompatEmbeddingsAPI
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppOutputs


async def get_tei_outputs(
    helm_values: dict[str, t.Any],
) -> dict[str, t.Any]:
    labels = {"application": "tei"}
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_api = None
    hf_model = helm_values.get("model")
    if internal_host:
        internal_api = OpenAICompatEmbeddingsAPI(
            host=internal_host,
            port=int(internal_port),
            protocol="http",
            hf_model=HuggingFaceModel.model_validate(hf_model) if hf_model else None,
        )

    host_port = await get_ingress_host_port(match_labels=labels)
    external_api = None
    if host_port:
        host, port = host_port
        external_api = OpenAICompatEmbeddingsAPI(
            host=host,
            port=int(port),
            protocol="https",
            hf_model=HuggingFaceModel.model_validate(hf_model) if hf_model else None,
        )
    outputs = TextEmbeddingsInferenceAppOutputs(
        internal_api=internal_api,
        external_api=external_api,
    )
    return outputs.model_dump()
