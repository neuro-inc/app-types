import pytest

from apolo_app_types import CrunchyPostgresUserCredentials, HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.common.ingress import AuthIngressMiddleware
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.openwebui import (
    AdvancedNetworkConfig,
    DataBaseConfig,
    NetworkConfig,
    OpenWebUIAppInputs,
    PostgresDatabase,
)

from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
)


@pytest.mark.asyncio
async def test_openwebui_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=OpenWebUIAppInputs(
            preset=Preset(name="cpu-small"),
            networking_config=NetworkConfig(
                ingress_http=IngressHttp(),
                advanced_networking=AdvancedNetworkConfig(),
            ),
            llm_chat_api=OpenAICompatChatAPI(
                host="llm-host",
                port=8000,
                protocol="https",
                base_path="/",
                hf_model=HuggingFaceModel(
                    model_hf_name="llm-model",
                ),
            ),
            database_config=DataBaseConfig(
                database=PostgresDatabase(
                    credentials=CrunchyPostgresUserCredentials(
                        user="pgvector_user",
                        password="pgvector_password",
                        host="pgvector_host",
                        port=5432,
                        pgbouncer_host="pgbouncer_host",
                        pgbouncer_port=4321,
                        dbname="db_name",
                    )
                )
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
        {
            "name": "DATABASE_URL",
            "value": "postgresql://pgvector_user:pgvector_password@pgbouncer_host:4321/db_name",
        },  # no url on app install, only outputs
        {
            "name": "VECTOR_DB",
            "value": "pgvector",
        },  # no url on app install, only outputs
        {
            "name": "PGVECTOR_DB_URL",
            "value": "postgresql://pgvector_user:pgvector_password@pgbouncer_host:4321/db_name",
        },  # no url on app install, only outputs
    ]


@pytest.mark.asyncio
async def test_openwebui_values_generation_with_ingress_middleware(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=OpenWebUIAppInputs(
            preset=Preset(name="cpu-small"),
            networking_config=NetworkConfig(
                ingress_http=IngressHttp(),
                advanced_networking=AdvancedNetworkConfig(
                    ingress_middleware=AuthIngressMiddleware(
                        name="platform-custom-auth-middleware"
                    )
                ),
            ),
            llm_chat_api=OpenAICompatChatAPI(
                host="llm-host",
                port=8000,
                protocol="https",
                base_path="/",
                hf_model=HuggingFaceModel(
                    model_hf_name="llm-model",
                ),
            ),
            database_config=DataBaseConfig(
                database=PostgresDatabase(
                    credentials=CrunchyPostgresUserCredentials(
                        user="pgvector_user",
                        password="pgvector_password",
                        host="pgvector_host",
                        port=5432,
                        pgbouncer_host="pgbouncer_host",
                        pgbouncer_port=4321,
                        dbname="db_name",
                    )
                )
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

    # Test that ingress is enabled
    assert helm_params["ingress"]["enabled"] is True

    # Test that the custom middleware annotation is added
    assert "annotations" in helm_params["ingress"]
    assert (
        "traefik.ingress.kubernetes.io/router.middlewares"
        in helm_params["ingress"]["annotations"]
    )

    # The middleware should contain both the default auth
    # middleware and our custom middleware
    middleware_annotation = helm_params["ingress"]["annotations"][
        "traefik.ingress.kubernetes.io/router.middlewares"
    ]
    expected_custom_middleware = "platform-custom-auth-middleware@kubernetescrd"

    # Should contain our custom middleware
    assert expected_custom_middleware in middleware_annotation
    # Should also contain the default auth middleware (since auth is
    # enabled by default)
    assert (
        "platform-platform-control-plane-ingress-auth@kubernetescrd"
        in middleware_annotation
    )

    # Test other basic functionality remains the same
    assert helm_params["image"] == {
        "repository": "ghcr.io/open-webui/open-webui",
        "tag": "git-b5f4c85",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["labels"] == {"application": "openwebui"}


@pytest.mark.asyncio
async def test_openwebui_values_generation_without_ingress_middleware(setup_clients):
    """Test that OpenWebUI works correctly when no ingress middleware is specified."""
    helm_args, helm_params = await app_type_to_vals(
        input_=OpenWebUIAppInputs(
            preset=Preset(name="cpu-small"),
            networking_config=NetworkConfig(
                ingress_http=IngressHttp(),
                advanced_networking=AdvancedNetworkConfig(
                    ingress_middleware=None  # Explicitly set to None
                ),
            ),
            llm_chat_api=OpenAICompatChatAPI(
                host="llm-host",
                port=8000,
                protocol="https",
                base_path="/",
                hf_model=HuggingFaceModel(
                    model_hf_name="llm-model",
                ),
            ),
            database_config=DataBaseConfig(
                database=PostgresDatabase(
                    credentials=CrunchyPostgresUserCredentials(
                        user="pgvector_user",
                        password="pgvector_password",
                        host="pgvector_host",
                        port=5432,
                        pgbouncer_host="pgbouncer_host",
                        pgbouncer_port=4321,
                        dbname="db_name",
                    )
                )
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

    # Test that ingress is enabled
    assert helm_params["ingress"]["enabled"] is True

    # Test that no custom middleware annotation is added when
    # ingress_middleware is None
    # (the ingress should still have annotations from the default
    # auth middleware if auth is enabled)
    if "annotations" in helm_params["ingress"]:
        middleware_annotation = helm_params["ingress"]["annotations"].get(
            "traefik.ingress.kubernetes.io/router.middlewares"
        )
        # Should not contain our custom middleware name
        if middleware_annotation:
            assert "custom-auth-middleware" not in middleware_annotation

    # Test other basic functionality remains the same
    assert helm_params["image"] == {
        "repository": "ghcr.io/open-webui/open-webui",
        "tag": "git-b5f4c85",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["labels"] == {"application": "openwebui"}
