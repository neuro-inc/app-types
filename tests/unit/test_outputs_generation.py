import pytest

from apolo_app_types.outputs.llm import get_llm_inference_outputs
from apolo_app_types.outputs.stable_diffusion import get_stable_diffusion_outputs
from apolo_app_types.outputs.weaviate import get_weaviate_outputs


@pytest.mark.asyncio
async def test_output_values_weaviate(setup_clients, mock_kubernetes_client):
    res = await get_weaviate_outputs(
        {
            "nameOverride": "weaviate",
            "clusterApi": {
                "username": "admin",
                "password": "admin",
            },
            "ingress": {"enabled": True},
        }
    )
    assert res["auth"] == {
        "username": "admin",
        "password": "admin",
    }
    assert res["external_rest_endpoint"]
    assert res["external_rest_endpoint"]["host"] == "example.com"
    assert res["external_rest_endpoint"]["base_path"] == "/v1"
    assert res["external_rest_endpoint"]["protocol"] == "https"
    assert res["external_graphql_endpoint"]["host"] == "example.com"
    assert res["external_graphql_endpoint"]["base_path"] == "/v1/graphql"
    assert res["internal_graphql_endpoint"]["host"] == "weaviate.default-namespace"
    assert res["internal_grpc_endpoint"]["host"] == "weaviate-grpc.default-namespace"
    assert res["internal_grpc_endpoint"]["port"] == 443


@pytest.mark.asyncio
async def test_output_values_weaviate_without_cluster_creds(
    setup_clients, mock_kubernetes_client
):
    res = await get_weaviate_outputs(
        {
            "ingress": {"enabled": True},
        }
    )
    assert res["auth"] == {
        "username": "",
        "password": "",
    }


@pytest.mark.asyncio
async def test_llm(setup_clients, mock_kubernetes_client):
    res = await get_llm_inference_outputs(
        helm_values={
            "model": {
                "modelHFName": "meta-llama/Llama-3.1-8B-Instruct",
                "tokenizerHFName": "meta-llama/Llama-3.1-8B-Instruct",
            },
            "serverExtraArgs": ["--api-key dummy-api-key"],
            "env": {"VLLM_API_KEY": "dummy"},
        }
    )
    assert res["hf_model"] == {
        "modelHFName": "meta-llama/Llama-3.1-8B-Instruct",
        "modelFiles": None,
        "hfToken": None,
    }
    assert res["llm_specific"] == {
        "tokenizer_name": "meta-llama/Llama-3.1-8B-Instruct",
        "api_key": "dummy-api-key",
    }
    assert res["chat_internal_api"]["host"] == "llm-inference.default-namespace"
    assert res["chat_internal_api"]["base_path"] == "/v1/chat"
    assert res["embeddings_internal_api"]["host"] == "llm-inference.default-namespace"
    assert res["embeddings_internal_api"]["base_path"] == "/v1/embeddings"
    assert res["chat_external_api"]["host"] == "example.com"
    assert res["embeddings_external_api"]["host"] == "example.com"


@pytest.mark.asyncio
async def test_llm_without_server_args(setup_clients, mock_kubernetes_client):
    res = await get_llm_inference_outputs(
        helm_values={
            "model": {
                "modelHFName": "meta-llama/Llama-3.1-8B-Instruct",
                "tokenizerHFName": "meta-llama/Llama-3.1-8B-Instruct",
            },
            "env": {"VLLM_API_KEY": "dummy-api-key"},
        }
    )

    assert res["hf_model"] == {
        "modelHFName": "meta-llama/Llama-3.1-8B-Instruct",
        "modelFiles": None,
        "hfToken": None,
    }
    assert res["llm_specific"] == {
        "tokenizer_name": "meta-llama/Llama-3.1-8B-Instruct",
        "api_key": "dummy-api-key",
    }
    assert res["chat_internal_api"]["host"] == "llm-inference.default-namespace"
    assert res["chat_internal_api"]["base_path"] == "/v1/chat"
    assert res["embeddings_internal_api"]["host"] == "llm-inference.default-namespace"
    assert res["embeddings_internal_api"]["base_path"] == "/v1/embeddings"
    assert res["chat_external_api"]["host"] == "example.com"
    assert res["embeddings_external_api"]["host"] == "example.com"


@pytest.mark.asyncio
async def test_llm_without_model(setup_clients, mock_kubernetes_client):
    with pytest.raises(KeyError) as exc_info:
        await get_llm_inference_outputs(helm_values={"env": {"VLLM_API_KEY": "dummy"}})
    assert str(exc_info.value) == "'model'"


@pytest.mark.asyncio
async def test_sd(setup_clients, mock_kubernetes_client):
    res = await get_stable_diffusion_outputs(
        helm_values={
            "model": {"modelHFName": "SD-Model", "modelFiles": "some_file"},
            "env": {"VLLM_API_KEY": "dummy-api-key"},
        }
    )

    assert res
    assert res["external_api"]["host"] == "example.com"
    assert res["external_api"]["base_path"] == "/sdapi/v1"
    assert res["internal_api"]["host"] == "app.default-namespace"
    assert res["internal_api"]["base_path"] == "/sdapi/v1"
    assert res["hf_model"] == {
        "modelHFName": "SD-Model",
        "modelFiles": "some_file",
        "hfToken": None,
    }


@pytest.mark.asyncio
async def test_sd_without_files(setup_clients, mock_kubernetes_client):
    res = await get_stable_diffusion_outputs(
        helm_values={
            "model": {
                "modelHFName": "SD-Model",
            }
        }
    )

    assert res
    assert res["external_api"]["host"] == "example.com"
    assert res["external_api"]["base_path"] == "/sdapi/v1"
    assert res["internal_api"]["host"] == "app.default-namespace"
    assert res["internal_api"]["base_path"] == "/sdapi/v1"
    assert res["hf_model"] == {
        "modelHFName": "SD-Model",
        "hfToken": None,
        "modelFiles": None,
    }


@pytest.mark.asyncio
async def test_sd_without_model(setup_clients, mock_kubernetes_client):
    with pytest.raises(KeyError) as exc_info:
        await get_stable_diffusion_outputs(helm_values={})

    assert str(exc_info.value) == "'model'"
