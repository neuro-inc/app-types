import pytest

from apolo_app_types.outputs.llm import get_llm_inference_outputs


@pytest.mark.asyncio
async def test_llm(setup_clients, mock_kubernetes_client, app_instance_id):
    res = await get_llm_inference_outputs(
        helm_values={
            "model": {
                "modelHFName": "meta-llama/Llama-3.1-8B-Instruct",
                "tokenizerHFName": "meta-llama/Llama-3.1-8B-Instruct",
            },
            "serverExtraArgs": ["--api-key dummy-api-key"],
            "env": {"VLLM_API_KEY": "dummy"},
        },
        app_instance_id=app_instance_id,
    )
    assert res["hugging_face_model"] == {
        "model_hf_name": "meta-llama/Llama-3.1-8B-Instruct",
        "hf_token": None,
        "__type__": "HuggingFaceModel",
    }
    assert res["tokenizer_hf_name"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert res["server_extra_args"] == ["--api-key dummy-api-key"]
    assert res["llm_api_key"] == "dummy-api-key"
    assert res["chat_internal_api"]["host"] == "app.default-namespace"
    assert res["chat_internal_api"]["endpoint_url"] == "/v1/chat"
    assert res["embeddings_internal_api"]["host"] == "app.default-namespace"
    assert res["embeddings_internal_api"]["endpoint_url"] == "/v1/embeddings"
    assert res["chat_external_api"]["host"] == "example.com"
    assert res["embeddings_external_api"]["host"] == "example.com"


@pytest.mark.asyncio
async def test_llm_without_server_args(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    res = await get_llm_inference_outputs(
        helm_values={
            "model": {
                "modelHFName": "meta-llama/Llama-3.1-8B-Instruct",
                "tokenizerHFName": "meta-llama/Llama-3.1-8B-Instruct",
            },
            "env": {"VLLM_API_KEY": "dummy-api-key"},
        },
        app_instance_id=app_instance_id,
    )

    assert res["hugging_face_model"] == {
        "model_hf_name": "meta-llama/Llama-3.1-8B-Instruct",
        "hf_token": None,
        "__type__": "HuggingFaceModel",
    }
    assert res["tokenizer_hf_name"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert not res["server_extra_args"]
    assert res["llm_api_key"] == "dummy-api-key"
    assert res["chat_internal_api"]["host"] == "app.default-namespace"
    assert res["chat_internal_api"]["endpoint_url"] == "/v1/chat"
    assert res["embeddings_internal_api"]["host"] == "app.default-namespace"
    assert res["embeddings_internal_api"]["endpoint_url"] == "/v1/embeddings"
    assert res["chat_external_api"]["host"] == "example.com"
    assert res["embeddings_external_api"]["host"] == "example.com"


@pytest.mark.asyncio
async def test_llm_without_model(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    with pytest.raises(KeyError) as exc_info:
        await get_llm_inference_outputs(
            helm_values={"env": {"VLLM_API_KEY": "dummy"}},
            app_instance_id=app_instance_id,
        )
    assert str(exc_info.value) == "'model'"
