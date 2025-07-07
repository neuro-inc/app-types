import pytest

from apolo_app_types import CrunchyPostgresUserCredentials, HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.openwebui import OpenWebUIAppInputs

from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
)


@pytest.mark.asyncio
async def test_openwebui_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=OpenWebUIAppInputs(
            preset=Preset(name="cpu-small"),
            ingress_http=IngressHttp(),
            llm_chat_api=OpenAICompatChatAPI(
                host="llm-host",
                port=8000,
                protocol="https",
                base_path="/",
                hf_model=HuggingFaceModel(
                    model_hf_name="llm-model",
                    tokenizer_hf_name="llm-tokenizer",
                ),
            ),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="pgvector_user",
                password="pgvector_password",
                host="pgvector_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=4321,
                dbname="db_name",
            ),
            embeddings_api=OpenAICompatEmbeddingsAPI(
                host="text-embeddings-inference-host",
                port=3000,
                protocol="https",
                base_path="/",
                hf_model=HuggingFaceModel(
                    model_hf_name="text-embeddings-inference-model",
                ),
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.OpenWebUI,
        app_name="openwebui-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/open-webui/open-webui",
        "tag": "git-b5f4c85",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["ingress"]["enabled"] is True

    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"containerPort": 8080, "name": "http"}],
    }
    assert helm_params["labels"] == {"application": "openwebui"}
    assert helm_params["container"]["env"] == [
        {"name": "OPENAI_API_BASE_URL", "value": "https://llm-host:8000/v1"},
        {"name": "RAG_EMBEDDING_ENGINE", "value": "openai"},
        {
            "name": "RAG_OPENAI_API_BASE_URL",
            "value": "https://text-embeddings-inference-host:3000/v1",
        },
        {"name": "DATABASE_URL", "value": ""},  # no url on app install, only outputs
        {
            "name": "VECTOR_DB",
            "value": "pgvector",
        },  # no url on app install, only outputs
        {"name": "PGVECTOR_DB_URL", "value": ""},  # no url on app install, only outputs
    ]
