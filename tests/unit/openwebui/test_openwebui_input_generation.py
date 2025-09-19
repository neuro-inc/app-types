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
    SQLiteDatabase,
)

from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
)


# Constants
DEFAULT_POSTGRES_CREDS = CrunchyPostgresUserCredentials(
    user="pgvector_user",
    password="pgvector_password",
    host="pgvector_host",
    port=5432,
    pgbouncer_host="pgbouncer_host",
    pgbouncer_port=4321,
    dbname="db_name",
)

TEST_POSTGRES_CREDS = CrunchyPostgresUserCredentials(
    user="test_pgvector_user",
    password="test_pgvector_password",
    host="test_pgvector_host",
    port=5432,
    pgbouncer_host="test_pgbouncer_host",
    pgbouncer_port=6543,
    dbname="test_db_name",
)

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


def create_database_config(db_type: str, *, use_test_creds: bool = False):
    """Factory for creating database configurations."""
    if db_type == "sqlite":
        return DataBaseConfig(database=SQLiteDatabase())
    if db_type == "postgres":
        creds = TEST_POSTGRES_CREDS if use_test_creds else DEFAULT_POSTGRES_CREDS
        return DataBaseConfig(database=PostgresDatabase(credentials=creds))
    msg = f"Unknown database type: {db_type}"
    raise ValueError(msg)


def create_openwebui_inputs(
    *,
    auth_enabled: bool = True,
    middleware_name: str | None = None,
    database_type: str = "postgres",
    use_test_db_creds: bool = False,
):
    """Factory for creating OpenWebUIAppInputs with specified configurations."""
    middleware = None
    if middleware_name:
        middleware = AuthIngressMiddleware(name=middleware_name)

    return OpenWebUIAppInputs(
        preset=Preset(name="cpu-small"),
        networking_config=NetworkConfig(
            ingress_http=IngressHttp(auth=auth_enabled),
            advanced_networking=AdvancedNetworkConfig(ingress_middleware=middleware),
        ),
        llm_chat_api=LLM_API_CONFIG,
        database_config=create_database_config(
            database_type, use_test_creds=use_test_db_creds
        ),
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


@pytest.mark.parametrize(
    (
        "auth_enabled",
        "middleware_name",
        "database_type",
        "expected_middleware",
        "should_fail",
    ),
    [
        # Auth enabled cases
        pytest.param(
            True,
            None,
            "postgres",
            ["platform-platform-control-plane-ingress-auth"],
            False,
            id="auth_enabled_no_middleware_postgres",
        ),
        pytest.param(
            True,
            "platform-custom-auth-middleware",
            "postgres",
            [
                "platform-platform-control-plane-ingress-auth",
                "platform-custom-auth-middleware",
            ],
            False,
            id="auth_enabled_with_middleware_postgres",
        ),
        pytest.param(
            True,
            None,
            "sqlite",
            ["platform-platform-control-plane-ingress-auth"],
            False,
            id="auth_enabled_no_middleware_sqlite",
        ),
        pytest.param(
            True,
            "platform-custom-rate-limiting-middleware",
            "sqlite",
            [
                "platform-platform-control-plane-ingress-auth",
                "platform-custom-rate-limiting-middleware",
            ],
            False,
            id="auth_enabled_with_middleware_sqlite",
        ),
        # Auth disabled cases
        pytest.param(
            False, None, "sqlite", [], False, id="auth_disabled_no_middleware_sqlite"
        ),
        pytest.param(
            False,
            "platform-custom-rate-limiting-middleware",
            "sqlite",
            ["platform-custom-rate-limiting-middleware"],
            True,
            id="auth_disabled_with_middleware_sqlite_xfail",
        ),
    ],
)
@pytest.mark.asyncio
async def test_openwebui_configuration_matrix(
    setup_clients,
    auth_enabled,
    middleware_name,
    database_type,
    expected_middleware,
    should_fail,
):
    """Test OpenWebUI input generation across auth, middleware, and database configs."""

    if should_fail:
        pytest.xfail(
            "Bug: OpenWebUI doesn't handle annotations when auth=False with middleware"
        )

    inputs = create_openwebui_inputs(
        auth_enabled=auth_enabled,
        middleware_name=middleware_name,
        database_type=database_type,
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
        helm_params, expected_middleware, auth_enabled=auth_enabled
    )

    # Assert database-specific configuration
    assert_database_env_vars(helm_params, database_type)


@pytest.mark.parametrize(
    ("database_type", "expected_db_url"),
    [
        pytest.param("sqlite", None, id="sqlite_database"),
        pytest.param(
            "postgres",
            "postgresql://test_pgvector_user:test_pgvector_password@test_pgbouncer_host:6543/test_db_name",
            id="postgres_database",
        ),
    ],
)
@pytest.mark.asyncio
async def test_openwebui_database_env_vars(
    setup_clients, database_type, expected_db_url
):
    """Test database-specific environment variable configuration."""

    inputs = create_openwebui_inputs(
        database_type=database_type,
        use_test_db_creds=True,  # Use test credentials for clearer assertions
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

    # Assert database-specific environment variables with expected URL
    assert_database_env_vars(helm_params, database_type, expected_db_url)


# Legacy individual tests for specific edge cases that don't fit the matrix well
@pytest.mark.asyncio
async def test_openwebui_values_generation_without_ingress_middleware(setup_clients):
    """Test OpenWebUI when ingress middleware is explicitly set to None."""
    inputs = create_openwebui_inputs(auth_enabled=True, middleware_name=None)

    # Explicitly set middleware to None to test this specific case
    inputs.networking_config.advanced_networking.ingress_middleware = None

    _, helm_params = await app_type_to_vals(
        input_=inputs,
        apolo_client=setup_clients,
        app_type=AppType.OpenWebUI,
        app_name="openwebui-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Test that ingress is enabled
    assert helm_params["ingress"]["enabled"] is True

    # Test that no custom middleware annotation is added when ingress_middleware is None
    if "annotations" in helm_params["ingress"]:
        middleware_annotation = helm_params["ingress"]["annotations"].get(
            "traefik.ingress.kubernetes.io/router.middlewares"
        )
        # Should not contain our custom middleware name
        if middleware_annotation:
            assert "custom-auth-middleware" not in middleware_annotation

    # Test other basic functionality remains the same
    assert_basic_helm_params(helm_params)
