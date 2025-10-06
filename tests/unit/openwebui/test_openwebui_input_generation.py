import pytest

from apolo_app_types import HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import (
    ApoloAuth,
    CustomAuth,
    IngressHttp,
    NoAuth,
    Preset,
)
from apolo_app_types.protocols.common.ingress import (
    AuthIngressMiddleware,
    BasicNetworkingConfig,
)
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.openwebui import (
    DataBaseConfig,
    OpenWebUIAppInputs,
    PostgresDatabase,
    SQLiteDatabase,
)

from tests.unit.conftest import (
    OpenWebUITestCase,
)
from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
    DEFAULT_AUTH_MIDDLEWARE,
    DEFAULT_POSTGRES_CREDS,
)


# Constants


LLM_API_CONFIG = OpenAICompatChatAPI(
    host="llm-host",
    port=8000,
    protocol="https",
    base_path="/",
    hf_model=HuggingFaceModel(model_hf_name="llm-model"),
)

EMBEDDINGS_API_CONFIG = OpenAICompatEmbeddingsAPI(
    host="text-embeddings-inference-host",
    port=3000,
    protocol="https",
    base_path="/",
    hf_model=HuggingFaceModel(model_hf_name="text-embeddings-inference-model"),
)

EXPECTED_IMAGE = {
    "repository": "ghcr.io/open-webui/open-webui",
    "tag": "git-b5f4c85",
    "pullPolicy": "IfNotPresent",
}

EXPECTED_SERVICE = {
    "enabled": True,
    "ports": [{"containerPort": 8080, "name": "http"}],
}

# Test configuration constants (imported from conftest.py)


def with_auth_middleware(*additional_middleware: str) -> list[str]:
    """Helper to create expected middleware lists with default auth middleware."""
    return [DEFAULT_AUTH_MIDDLEWARE, *additional_middleware]


def create_database_config(db_type: str):
    """Factory for creating database configurations."""
    if db_type == "sqlite":
        return DataBaseConfig(database=SQLiteDatabase())
    if db_type == "postgres":
        return DataBaseConfig(
            database=PostgresDatabase(credentials=DEFAULT_POSTGRES_CREDS)
        )
    msg = f"Unknown database type: {db_type}"
    raise ValueError(msg)


def create_openwebui_inputs(
    *,
    auth_enabled: bool = True,
    middleware_name: str | None = None,
    database_type: str = "postgres",
):
    """Factory for creating OpenWebUIAppInputs with specified configurations."""
    # Determine auth type based on parameters
    if middleware_name:
        auth = CustomAuth(middleware=AuthIngressMiddleware(name=middleware_name))
    elif auth_enabled:
        auth = ApoloAuth()
    else:
        auth = NoAuth()

    return OpenWebUIAppInputs(
        preset=Preset(name="cpu-small"),
        networking_config=BasicNetworkingConfig(
            ingress_http=IngressHttp(auth=auth),
        ),
        llm_chat_api=LLM_API_CONFIG,
        database_config=create_database_config(database_type),
        embeddings_api=EMBEDDINGS_API_CONFIG,
    )


def assert_basic_helm_params(helm_params):
    """Assert common helm parameters that should be present in all tests."""
    assert helm_params["image"] == EXPECTED_IMAGE
    assert helm_params["ingress"]["enabled"] is True
    assert helm_params["service"] == EXPECTED_SERVICE
    assert helm_params["labels"] == {"application": "openwebui"}


def assert_common_env_vars(helm_params):
    """Assert environment variables that should be present in all configurations."""
    env_vars = helm_params["container"]["env"]

    # Check for OpenAI API configuration
    openai_base_url = next(
        (env for env in env_vars if env["name"] == "OPENAI_API_BASE_URL"), None
    )
    assert openai_base_url is not None
    assert openai_base_url["value"] == "https://llm-host:8000/v1"

    # Check for embeddings configuration
    rag_engine = next(
        (env for env in env_vars if env["name"] == "RAG_EMBEDDING_ENGINE"), None
    )
    assert rag_engine is not None
    assert rag_engine["value"] == "openai"

    rag_base_url = next(
        (env for env in env_vars if env["name"] == "RAG_OPENAI_API_BASE_URL"), None
    )
    assert rag_base_url is not None
    assert rag_base_url["value"] == "https://text-embeddings-inference-host:3000/v1"


def assert_middleware_annotations(
    helm_params, expected_middleware_names: list[str], *, auth_enabled: bool
):
    """Assert middleware annotations based on expected configuration."""
    if not expected_middleware_names:
        # When no middleware is expected
        if "annotations" in helm_params["ingress"]:
            middleware_annotation = helm_params["ingress"]["annotations"].get(
                "traefik.ingress.kubernetes.io/router.middlewares"
            )
            if middleware_annotation and not auth_enabled:
                # For auth disabled cases, should not contain auth middleware
                assert (
                    "platform-control-plane-ingress-auth" not in middleware_annotation
                )
                assert "custom-auth-middleware" not in middleware_annotation
        return

    # When middleware is expected
    assert "annotations" in helm_params["ingress"]
    assert (
        "traefik.ingress.kubernetes.io/router.middlewares"
        in helm_params["ingress"]["annotations"]
    )

    middleware_annotation = helm_params["ingress"]["annotations"][
        "traefik.ingress.kubernetes.io/router.middlewares"
    ]

    for middleware_name in expected_middleware_names:
        expected_middleware = f"{middleware_name}@kubernetescrd"
        assert expected_middleware in middleware_annotation


def assert_database_env_vars(
    helm_params, database_type: str, expected_db_url: str | None = None
):
    """Assert database-specific environment variables."""
    env_vars = helm_params["container"]["env"]

    if database_type == "sqlite":
        # For SQLite, DATABASE_URL should not be set (or should be empty/default)
        database_url = next(
            (env for env in env_vars if env["name"] == "DATABASE_URL"), None
        )
        if database_url is not None:
            # SQLite should use local file, not external database URL
            assert not database_url["value"].startswith("postgresql://")

        # VECTOR_DB and PGVECTOR_DB_URL should not be set for SQLite
        vector_db = next((env for env in env_vars if env["name"] == "VECTOR_DB"), None)
        if vector_db is not None:
            assert vector_db["value"] != "pgvector"

        pgvector_url = next(
            (env for env in env_vars if env["name"] == "PGVECTOR_DB_URL"), None
        )
        assert pgvector_url is None

    elif database_type == "postgres":
        # Check PostgreSQL database configuration
        database_url = next(
            (env for env in env_vars if env["name"] == "DATABASE_URL"), None
        )
        assert database_url is not None
        if expected_db_url:
            assert database_url["value"] == expected_db_url

        # Check vector database configuration for PostgreSQL
        vector_db = next((env for env in env_vars if env["name"] == "VECTOR_DB"), None)
        assert vector_db is not None
        assert vector_db["value"] == "pgvector"

        pgvector_url = next(
            (env for env in env_vars if env["name"] == "PGVECTOR_DB_URL"), None
        )
        assert pgvector_url is not None
        if expected_db_url:
            assert pgvector_url["value"] == expected_db_url


@pytest.mark.asyncio
async def test_openwebui_configuration_matrix(
    setup_clients, openwebui_test_case: OpenWebUITestCase
):
    """Test OpenWebUI input generation across auth, middleware, and database configs."""

    inputs = create_openwebui_inputs(
        auth_enabled=openwebui_test_case.auth_enabled,
        middleware_name=openwebui_test_case.middleware_name,
        database_type=openwebui_test_case.database_type,
    )

    _, helm_params = await app_type_to_vals(
        input_=inputs,
        apolo_client=setup_clients,
        app_type=AppType.OpenWebUI,
        app_name="openwebui-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Assert basic configuration
    assert_basic_helm_params(helm_params)

    # Assert common environment variables
    assert_common_env_vars(helm_params)

    # Assert middleware configuration
    assert_middleware_annotations(
        helm_params,
        openwebui_test_case.expected_middleware,
        auth_enabled=openwebui_test_case.auth_enabled,
    )

    # Assert database-specific configuration with URL assertions when available
    assert_database_env_vars(
        helm_params,
        openwebui_test_case.database_type,
        openwebui_test_case.expected_db_url,
    )
