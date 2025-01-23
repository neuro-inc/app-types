import typing as t

from apolo_app_types import VLLMOutputs, OpenAICompatibleChatAPI, OpenAICompatibleEmbeddingsAPI
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.outputs.utils.parsing import parse_cli_args, get_service_host_port



async def get_llm_inference_outputs(helm_values: dict[str, t.Any]) -> VLLMOutputs:
    internal_host, internal_port = await get_service_host_port(
        match_labels={"application": "llm-inference"}
    )

    cli_args = parse_cli_args(helm_values.get("serverExtraArgs", []))
    # API key could be defined in server args or within envs.
    # The first one has higher priority
    api_key = cli_args.get("api-key") or helm_values.get("env", {}).get("VLLM_API_KEY")

    model_name = helm_values["model"]["modelHFName"]
    tokenizer_name = helm_values["model"].get("tokenizerHFName", "")

    chat_internal_api = OpenAICompatibleChatAPI(
        model_name=model_name,
        tokenizer_name=tokenizer_name,
        host=internal_host,
        port=internal_port,
        api_base=f"http://{internal_host}:{internal_port}/v1",
        api_key=api_key,
    )
    embeddings_internal_api = OpenAICompatibleEmbeddingsAPI(
        **chat_internal_api.model_dump()
    )

    ingress_host_port = await get_ingress_host_port(
        match_labels={"application": "llm-inference"}
    )
    chat_external_api = None
    embeddings_external_api = None
    if ingress_host_port:
        chat_external_api = OpenAICompatibleChatAPI(
            model_name=model_name,
            host=ingress_host_port[0],
            port=ingress_host_port[1],
            api_base=f"https://{ingress_host_port[0]}/v1",
            api_key=api_key,
        )
        embeddings_external_api = OpenAICompatibleEmbeddingsAPI(
            **chat_external_api.model_dump()
        )

    vllm_outputs = VLLMOutputs(
        chat_internal_api=chat_internal_api,
        chat_external_api=chat_external_api,
        embeddings_internal_api=embeddings_internal_api,
        embeddings_external_api=embeddings_external_api,
    )
    print("Outputs")
    print(vllm_outputs.model_dump())
    return vllm_outputs
