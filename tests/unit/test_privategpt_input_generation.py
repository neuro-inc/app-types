import pytest

from apolo_app_types import CrunchyPostgresUserCredentials, HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.common.networking import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.llm import LLMModel
from apolo_app_types.protocols.private_gpt import (
    PrivateGPTAppInputs,
    PrivateGptSpecific,
)

from tests.unit.constants import (
    APP_SECRETS_NAME,
)


@pytest.mark.asyncio
async def test_privategpt_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=PrivateGPTAppInputs(
            preset=Preset(name="cpu-small"),
            ingress=Ingress(
                enabled=True,
            ),
            llm_chat_api=OpenAICompatChatAPI(
                host="llm-host", port=8000, protocol="https", base_path="/"
            ),
            llm_details=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    model_hf_name="llm-model",
                    tokenizer_hf_name="llm-tokenizer",
                )
            ),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="pgvector_user",
                password="pgvector_password",
                host="pgvector_host",
                port="pgvector_port",
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port="pgbouncer_port",
            ),
            tei_api=OpenAICompatEmbeddingsAPI(
                host="text-embeddings-inference-host",
                port=3000,
                protocol="https",
                base_path="/",
            ),
            tei_model=HuggingFaceModel(
                model_hf_name="text-embeddings-inference-model",
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.PrivateGPT,
        app_name="privategpt-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/private-gpt",
        "tag": "latest",
    }
    assert helm_params["ingress"] == {
        "className": "traefik",
        "enabled": True,
        "grpc": {"enabled": False},
        "hosts": [
            {
                "host": "default-namespace.apps.some.org.neu.ro",
                "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
            }
        ],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"containerPort": 8080, "name": "http"}],
    }
    assert helm_params["labels"] == {"application": "privategpt"}
    assert helm_params["container"]["env"] == [
        {"name": "PGPT_PROFILES", "value": "app, pgvector"},
        {"name": "VLLM_API_BASE", "value": "https://llm-host:8000/"},
        {"name": "VLLM_MODEL", "value": "llm-model"},
        {"name": "VLLM_TOKENIZER", "value": "llm-model"},
        {"name": "VLLM_MAX_NEW_TOKENS", "value": "5000"},
        {"name": "VLLM_CONTEXT_WINDOW", "value": "8192"},
        {"name": "VLLM_TEMPERATURE", "value": "0.1"},
        {
            "name": "EMBEDDING_API_BASE",
            "value": "https://text-embeddings-inference-host:3000/",
        },
        {"name": "EMBEDDING_MODEL", "value": "text-embeddings-inference-model"},
        {"name": "EMBEDDING_DIM", "value": "768"},
        {"name": "POSTGRES_HOST", "value": "pgbouncer_host"},
        {"name": "POSTGRES_PORT", "value": "pgbouncer_port"},
        {"name": "POSTGRES_DB", "value": "None"},
        {"name": "POSTGRES_USER", "value": "pgvector_user"},
        {"name": "POSTGRES_PASSWORD", "value": "pgvector_password"},
    ]


@pytest.mark.asyncio
async def test_privategpt_values_generation_custom_temperature(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=PrivateGPTAppInputs(
            preset=Preset(name="cpu-small"),
            ingress=Ingress(
                enabled=True,
            ),
            llm_chat_api=OpenAICompatChatAPI(
                host="llm-host", port=8000, protocol="https", base_path="/"
            ),
            llm_details=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    model_hf_name="llm-model",
                    tokenizer_hf_name="llm-tokenizer",
                )
            ),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="pgvector_user",
                password="pgvector_password",
                host="pgvector_host",
                port="pgvector_port",
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port="pgbouncer_port",
            ),
            tei_api=OpenAICompatEmbeddingsAPI(
                host="text-embeddings-inference-host",
                port=3000,
                protocol="https",
                base_path="/",
            ),
            tei_model=HuggingFaceModel(
                model_hf_name="text-embeddings-inference-model",
            ),
            private_gpt_specific=PrivateGptSpecific(
                llm_temperature=0.5,
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.PrivateGPT,
        app_name="privategpt-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/private-gpt",
        "tag": "latest",
    }
    assert helm_params["ingress"] == {
        "className": "traefik",
        "enabled": True,
        "grpc": {"enabled": False},
        "hosts": [
            {
                "host": "default-namespace.apps.some.org.neu.ro",
                "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
            }
        ],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"containerPort": 8080, "name": "http"}],
    }
    assert helm_params["labels"] == {"application": "privategpt"}
    assert helm_params["container"]["env"] == [
        {"name": "PGPT_PROFILES", "value": "app, pgvector"},
        {"name": "VLLM_API_BASE", "value": "https://llm-host:8000/"},
        {"name": "VLLM_MODEL", "value": "llm-model"},
        {"name": "VLLM_TOKENIZER", "value": "llm-model"},
        {"name": "VLLM_MAX_NEW_TOKENS", "value": "5000"},
        {"name": "VLLM_CONTEXT_WINDOW", "value": "8192"},
        {"name": "VLLM_TEMPERATURE", "value": "0.5"},
        {
            "name": "EMBEDDING_API_BASE",
            "value": "https://text-embeddings-inference-host:3000/",
        },
        {"name": "EMBEDDING_MODEL", "value": "text-embeddings-inference-model"},
        {"name": "EMBEDDING_DIM", "value": "768"},
        {"name": "POSTGRES_HOST", "value": "pgbouncer_host"},
        {"name": "POSTGRES_PORT", "value": "pgbouncer_port"},
        {"name": "POSTGRES_DB", "value": "None"},
        {"name": "POSTGRES_USER", "value": "pgvector_user"},
        {"name": "POSTGRES_PASSWORD", "value": "pgvector_password"},
    ]
