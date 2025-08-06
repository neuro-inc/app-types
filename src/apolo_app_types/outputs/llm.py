import logging
import typing as t

from apolo_app_types import (
    HuggingFaceModel,
    VLLMOutputsV2,
)
from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import INSTANCE_LABEL
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.outputs.utils.parsing import parse_cli_args
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)


logger = logging.getLogger()


async def get_llm_inference_outputs(
    helm_values: dict[str, t.Any], app_instance_id: str
) -> dict[str, t.Any]:
    internal_host, internal_port = await get_service_host_port(
        match_labels={
            INSTANCE_LABEL: app_instance_id,
        }
    )
    server_extra_args = helm_values.get("serverExtraArgs", [])
    cli_args = parse_cli_args(server_extra_args)
    # API key could be defined in server args or within envs.
    # The first one has higher priority
    api_key = cli_args.get("api-key") or helm_values.get("env", {}).get("VLLM_API_KEY")

    model_name = helm_values["model"]["modelHFName"]
    tokenizer_name = helm_values["model"].get("tokenizerHFName", "")
    hf_model = HuggingFaceModel(
        model_hf_name=model_name,
    )
    chat_internal_api = OpenAICompatChatAPI(
        host=internal_host,
        port=int(internal_port),
        protocol="http",
        hf_model=hf_model,
    )
    embeddings_internal_api = OpenAICompatEmbeddingsAPI(
        host=internal_host,
        port=int(internal_port),
        protocol="http",
        hf_model=hf_model,
    )

    ingress_host_port = await get_ingress_host_port(
        match_labels={
            INSTANCE_LABEL: app_instance_id,
        }
    )
    chat_external_api = None
    embeddings_external_api = None
    if ingress_host_port:
        chat_external_api = OpenAICompatChatAPI(
            host=ingress_host_port[0],
            port=int(ingress_host_port[1]),
            protocol="https",
            hf_model=hf_model,
        )
        embeddings_external_api = OpenAICompatEmbeddingsAPI(
            host=ingress_host_port[0],
            port=int(ingress_host_port[1]),
            protocol="https",
            hf_model=hf_model,
        )

    vllm_outputs = VLLMOutputsV2(
        chat_internal_api=chat_internal_api,
        chat_external_api=chat_external_api,
        embeddings_internal_api=embeddings_internal_api,
        embeddings_external_api=embeddings_external_api,
        hugging_face_model=hf_model,
        tokenizer_hf_name=tokenizer_name,
        server_extra_args=server_extra_args,
        llm_api_key=api_key,
    )
    return vllm_outputs.model_dump()
