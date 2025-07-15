import pytest
from dirty_equals import IsStr

from apolo_app_types import CrunchyPostgresUserCredentials, HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.lightrag import (
    AnthropicLLMProvider,
    GeminiLLMProvider,
    LightRAGAppInputs,
    LightRAGPersistence,
    OllamaEmbeddingProvider,
    OllamaLLMProvider,
    OpenAIEmbeddingProvider,
    OpenAILLMProvider,
)

from tests.unit.constants import APP_ID, APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_lightrag_openai_llm_provider(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with OpenAI LLM provider"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-openai-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-3-small",
                api_key="test-openai-key",
                dimensions=1536,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify LLM configuration
    assert helm_params["env"]["LLM_BINDING"] == "openai"
    assert helm_params["env"]["LLM_MODEL"] == "gpt-4"
    assert helm_params["env"]["LLM_BINDING_HOST"] == "https://api.openai.com:443/v1"
    assert helm_params["env"]["LLM_BINDING_API_KEY"] == "test-openai-key"
    assert helm_params["env"]["OPENAI_API_KEY"] == "test-openai-key"

    # Verify embedding configuration
    assert helm_params["env"]["EMBEDDING_BINDING"] == "openai"
    assert helm_params["env"]["EMBEDDING_MODEL"] == "text-embedding-3-small"
    assert helm_params["env"]["EMBEDDING_DIM"] == 1536
    assert (
        helm_params["env"]["EMBEDDING_BINDING_HOST"] == "https://api.openai.com:443/v1"
    )
    assert helm_params["env"]["EMBEDDING_BINDING_API_KEY"] == "test-openai-key"


@pytest.mark.asyncio
async def test_lightrag_anthropic_llm_provider(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with Anthropic LLM provider"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=AnthropicLLMProvider(
                model="claude-3-opus-20240229",
                api_key="test-anthropic-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-openai-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify LLM configuration
    assert helm_params["env"]["LLM_BINDING"] == "anthropic"
    assert helm_params["env"]["LLM_MODEL"] == "claude-3-opus-20240229"
    assert helm_params["env"]["LLM_BINDING_HOST"] == "https://api.anthropic.com:443/v1"
    assert helm_params["env"]["LLM_BINDING_API_KEY"] == "test-anthropic-key"
    assert (
        helm_params["env"]["OPENAI_API_KEY"] == "test-anthropic-key"
    )  # OPENAI_API_KEY uses LLM provider key


@pytest.mark.asyncio
async def test_lightrag_ollama_providers(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with Ollama LLM and embedding providers"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OllamaLLMProvider(
                host="ollama.example.com",
                model="llama3.1:8b",
                port=11434,
            ),
            embedding_config=OllamaEmbeddingProvider(
                host="ollama.example.com",
                model="nomic-embed-text",
                port=11434,
                dimensions=1024,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify LLM configuration
    assert helm_params["env"]["LLM_BINDING"] == "ollama"
    assert helm_params["env"]["LLM_MODEL"] == "llama3.1:8b"
    assert (
        helm_params["env"]["LLM_BINDING_HOST"] == "http://ollama.example.com:11434/api"
    )
    assert helm_params["env"]["LLM_BINDING_API_KEY"] == ""
    assert helm_params["env"]["OPENAI_API_KEY"] == ""

    # Verify embedding configuration
    assert helm_params["env"]["EMBEDDING_BINDING"] == "ollama"
    assert helm_params["env"]["EMBEDDING_MODEL"] == "nomic-embed-text"
    assert helm_params["env"]["EMBEDDING_DIM"] == 1024
    assert (
        helm_params["env"]["EMBEDDING_BINDING_HOST"]
        == "http://ollama.example.com:11434/api"
    )
    assert helm_params["env"]["EMBEDDING_BINDING_API_KEY"] == ""


@pytest.mark.asyncio
async def test_lightrag_gemini_llm_provider(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with Gemini LLM provider"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=GeminiLLMProvider(
                model="gemini-1.5-pro",
                api_key="test-gemini-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-openai-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify LLM configuration
    assert helm_params["env"]["LLM_BINDING"] == "gemini"
    assert helm_params["env"]["LLM_MODEL"] == "gemini-1.5-pro"
    assert (
        helm_params["env"]["LLM_BINDING_HOST"]
        == "https://generativelanguage.googleapis.com:443/v1"
    )
    assert helm_params["env"]["LLM_BINDING_API_KEY"] == "test-gemini-key"


@pytest.mark.asyncio
async def test_lightrag_openai_compatible_providers(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with OpenAI compatible API providers"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAICompatChatAPI(
                host="my-llm-server.com",
                port=8080,
                protocol="https",
                hf_model=HuggingFaceModel(
                    model_hf_name="meta-llama/Llama-3.1-8B-Instruct",
                    hf_token="test-hf-token",
                ),
            ),
            embedding_config=OpenAICompatEmbeddingsAPI(
                host="my-embedding-server.com",
                port=8080,
                protocol="https",
                hf_model=HuggingFaceModel(
                    model_hf_name="sentence-transformers/all-MiniLM-L6-v2",
                    hf_token="test-hf-token",
                ),
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify LLM configuration
    assert helm_params["env"]["LLM_BINDING"] == "openai"
    assert helm_params["env"]["LLM_MODEL"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert helm_params["env"]["LLM_BINDING_HOST"] == "https://my-llm-server.com:8080/"
    assert helm_params["env"]["OPENAI_API_KEY"] == ""

    # Verify embedding configuration
    assert helm_params["env"]["EMBEDDING_BINDING"] == "openai"
    assert (
        helm_params["env"]["EMBEDDING_MODEL"]
        == "sentence-transformers/all-MiniLM-L6-v2"
    )
    assert helm_params["env"]["EMBEDDING_DIM"] == 1536
    assert (
        helm_params["env"]["EMBEDDING_BINDING_HOST"]
        == "https://my-embedding-server.com:8080/"
    )
    assert helm_params["env"]["EMBEDDING_BINDING_API_KEY"] == ""


@pytest.mark.asyncio
async def test_lightrag_secret_handling(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with ApoloSecret for API keys"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key=ApoloSecret(key="openai_api_key"),
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-3-small",
                api_key=ApoloSecret(key="openai_api_key"),
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify LLM configuration uses secret references
    assert helm_params["env"]["LLM_BINDING_API_KEY"] == {
        "valueFrom": {
            "secretKeyRef": {"name": APP_SECRETS_NAME, "key": "openai_api_key"}
        }
    }
    assert helm_params["env"]["OPENAI_API_KEY"] == {
        "valueFrom": {
            "secretKeyRef": {"name": APP_SECRETS_NAME, "key": "openai_api_key"}
        }
    }

    # Verify embedding configuration uses secret references
    assert helm_params["env"]["EMBEDDING_BINDING_API_KEY"] == {
        "valueFrom": {
            "secretKeyRef": {"name": APP_SECRETS_NAME, "key": "openai_api_key"}
        }
    }


@pytest.mark.asyncio
async def test_lightrag_persistence_configuration(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with custom persistence configuration"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-key",
            ),
            persistence=LightRAGPersistence(
                rag_storage_size=20,
                inputs_storage_size=10,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify persistence configuration
    assert helm_params["persistence"]["enabled"] is True
    assert helm_params["persistence"]["ragStorage"]["size"] == "20Gi"
    assert helm_params["persistence"]["inputs"]["size"] == "10Gi"


@pytest.mark.asyncio
async def test_lightrag_postgres_configuration(setup_clients, mock_get_preset_cpu):
    """Test LightRAG PostgreSQL configuration"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="lightrag_user",
                password="lightrag_password",
                host="postgres.example.com",
                port=5432,
                pgbouncer_host="pgbouncer.example.com",
                pgbouncer_port=6432,
                dbname="lightrag_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify PostgreSQL configuration
    assert helm_params["env"]["POSTGRES_HOST"] == "pgbouncer.example.com"
    assert helm_params["env"]["POSTGRES_PORT"] == 6432
    assert helm_params["env"]["POSTGRES_USER"] == "lightrag_user"
    assert helm_params["env"]["POSTGRES_PASSWORD"] == "lightrag_password"
    assert helm_params["env"]["POSTGRES_DATABASE"] == "lightrag_db"
    assert helm_params["env"]["POSTGRES_WORKSPACE"] == "default"


@pytest.mark.asyncio
async def test_lightrag_storage_configuration(setup_clients, mock_get_preset_cpu):
    """Test LightRAG storage configuration"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify storage configuration
    assert helm_params["env"]["LIGHTRAG_KV_STORAGE"] == "PGKVStorage"
    assert helm_params["env"]["LIGHTRAG_VECTOR_STORAGE"] == "PGVectorStorage"
    assert helm_params["env"]["LIGHTRAG_DOC_STATUS_STORAGE"] == "PGDocStatusStorage"
    assert helm_params["env"]["LIGHTRAG_GRAPH_STORAGE"] == "NetworkXStorage"


@pytest.mark.asyncio
async def test_lightrag_web_ui_configuration(setup_clients, mock_get_preset_cpu):
    """Test LightRAG web UI configuration"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify web UI configuration
    assert helm_params["env"]["WEBUI_TITLE"] == "Graph RAG Engine"
    assert (
        helm_params["env"]["WEBUI_DESCRIPTION"]
        == "Simple and Fast Graph Based RAG System"
    )
    assert helm_params["env"]["HOST"] == "0.0.0.0"
    assert helm_params["env"]["PORT"] == 9621


@pytest.mark.asyncio
async def test_lightrag_basic_chart_values(setup_clients, mock_get_preset_cpu):
    """Test LightRAG basic chart values"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-ada-002",
                api_key="test-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify basic chart values
    assert helm_params["replicaCount"] == 1
    assert helm_params["image"]["repository"] == "ghcr.io/hkuds/lightrag"
    assert helm_params["image"]["tag"] == "1.3.8"
    assert helm_params["image"]["pullPolicy"] == "IfNotPresent"
    assert helm_params["service"]["type"] == "ClusterIP"
    assert helm_params["service"]["port"] == 9621
    assert helm_params["fullnameOverride"] == "lightrag-test"
    assert helm_params["apolo_app_id"] == APP_ID
    assert helm_params["appTypesImage"]["tag"] == IsStr(regex=r"^v\d+\.\d+\.\d+.*$")


@pytest.mark.asyncio
async def test_lightrag_embedding_dimensions(setup_clients, mock_get_preset_cpu):
    """Test LightRAG embedding dimensions are set correctly"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OpenAILLMProvider(
                model="gpt-4",
                api_key="test-key",
            ),
            embedding_config=OpenAIEmbeddingProvider(
                model="text-embedding-3-large",
                api_key="test-key",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify embedding dimensions use default values
    assert helm_params["env"]["EMBEDDING_DIM"] == 1536


@pytest.mark.asyncio
async def test_lightrag_ollama_embedding_dimensions(setup_clients, mock_get_preset_cpu):
    """Test LightRAG with Ollama embedding dimensions"""
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LightRAGAppInputs(
            preset=Preset(name="cpu-large"),
            ingress_http=IngressHttp(),
            pgvector_user=CrunchyPostgresUserCredentials(
                user="test_user",
                password="test_password",
                host="postgres_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=6432,
                dbname="test_db",
            ),
            llm_config=OllamaLLMProvider(
                host="ollama.example.com",
                model="llama3.1:8b",
            ),
            embedding_config=OllamaEmbeddingProvider(
                host="ollama.example.com",
                model="mxbai-embed-large",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LightRAG,
        app_name="lightrag-test",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Verify Ollama embedding dimensions use default values
    assert helm_params["env"]["EMBEDDING_DIM"] == 1024


@pytest.mark.asyncio
async def test_lightrag_error_handling_missing_hf_model(
    setup_clients, mock_get_preset_cpu
):
    """Test LightRAG error handling for missing hf_model in OpenAI compatible API"""
    apolo_client = setup_clients

    with pytest.raises(
        ValueError, match="OpenAI compatible chat API must have hf_model configured"
    ):
        await app_type_to_vals(
            input_=LightRAGAppInputs(
                preset=Preset(name="cpu-large"),
                ingress_http=IngressHttp(),
                pgvector_user=CrunchyPostgresUserCredentials(
                    user="test_user",
                    password="test_password",
                    host="postgres_host",
                    port=5432,
                    pgbouncer_host="pgbouncer_host",
                    pgbouncer_port=6432,
                    dbname="test_db",
                ),
                llm_config=OpenAICompatChatAPI(
                    host="my-llm-server.com",
                    hf_model=None,  # This should cause an error
                ),
                embedding_config=OpenAIEmbeddingProvider(
                    model="text-embedding-ada-002",
                    api_key="test-key",
                ),
            ),
            apolo_client=apolo_client,
            app_type=AppType.LightRAG,
            app_name="lightrag-test",
            namespace=DEFAULT_NAMESPACE,
            app_secrets_name=APP_SECRETS_NAME,
            app_id=APP_ID,
        )


@pytest.mark.asyncio
async def test_lightrag_error_handling_missing_embedding_hf_model(
    setup_clients, mock_get_preset_cpu
):
    """Test LightRAG error handling for missing hf_model in
    OpenAI compatible embeddings API"""
    apolo_client = setup_clients

    with pytest.raises(
        ValueError,
        match="OpenAI compatible embeddings API must have hf_model configured",
    ):
        await app_type_to_vals(
            input_=LightRAGAppInputs(
                preset=Preset(name="cpu-large"),
                ingress_http=IngressHttp(),
                pgvector_user=CrunchyPostgresUserCredentials(
                    user="test_user",
                    password="test_password",
                    host="postgres_host",
                    port=5432,
                    pgbouncer_host="pgbouncer_host",
                    pgbouncer_port=6432,
                    dbname="test_db",
                ),
                llm_config=OpenAILLMProvider(
                    model="gpt-4",
                    api_key="test-key",
                ),
                embedding_config=OpenAICompatEmbeddingsAPI(
                    host="my-embedding-server.com",
                    hf_model=None,  # This should cause an error
                ),
            ),
            apolo_client=apolo_client,
            app_type=AppType.LightRAG,
            app_name="lightrag-test",
            namespace=DEFAULT_NAMESPACE,
            app_secrets_name=APP_SECRETS_NAME,
            app_id=APP_ID,
        )


def test_lightrag_persistence_validation():
    """Test LightRAG persistence validation"""
    # Test valid persistence
    persistence = LightRAGPersistence(rag_storage_size=10, inputs_storage_size=5)
    assert persistence.rag_storage_size == 10
    assert persistence.inputs_storage_size == 5

    # Test invalid storage size (0 is falsy, so it goes to "must be specified as int")
    with pytest.raises(ValueError, match="Storage size must be specified as int"):
        LightRAGPersistence(rag_storage_size=0, inputs_storage_size=5)

    # Test negative storage size
    with pytest.raises(ValueError, match="Storage size must be greater than 1GB"):
        LightRAGPersistence(rag_storage_size=-1, inputs_storage_size=5)
