import logging
import typing as t

from apolo_app_types import LightRAGAppInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_extra_values,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.lightrag import (
    AnthropicLLMProvider,
    GeminiLLMProvider,
    OllamaEmbeddingProvider,
    OllamaLLMProvider,
    OpenAIEmbeddingProvider,
    OpenAILLMProvider,
)


logger = logging.getLogger(__name__)


class LightRAGChartValueProcessor(BaseChartValueProcessor[LightRAGAppInputs]):
    def _extract_llm_config(self, llm_config: t.Any) -> dict[str, t.Any]:
        """Extract LLM configuration from provider-specific config."""
        if isinstance(llm_config, OpenAICompatChatAPI):
            # For OpenAI compatible API, always use hf_model.model_hf_name
            if not llm_config.hf_model:
                msg = "OpenAI compatible chat API must have hf_model configured"
                raise ValueError(msg)
            model = llm_config.hf_model.model_hf_name
            host = llm_config.complete_url
            return {
                "binding": "openai",
                "model": model,
                "host": host,
                "api_key": getattr(llm_config, "api_key", None),
            }
        if isinstance(llm_config, OpenAILLMProvider):
            host = llm_config.complete_url
            return {
                "binding": "openai",
                "model": llm_config.model,
                "host": host,
                "api_key": llm_config.api_key,
            }
        if isinstance(llm_config, AnthropicLLMProvider):
            host = llm_config.complete_url
            return {
                "binding": "anthropic",
                "model": llm_config.model,
                "host": host,
                "api_key": llm_config.api_key,
            }
        if isinstance(llm_config, OllamaLLMProvider):
            host = llm_config.complete_url
            return {
                "binding": "ollama",
                "model": llm_config.model,
                "host": host,
                "api_key": None,
            }
        if isinstance(llm_config, GeminiLLMProvider):
            host = llm_config.complete_url
            return {
                "binding": "gemini",
                "model": llm_config.model,
                "host": host,
                "api_key": llm_config.api_key,
            }
        # Fallback to generic extraction
        binding = getattr(llm_config, "provider", "openai")
        model = getattr(llm_config, "model", "gpt-4o-mini")
        api_key = getattr(llm_config, "api_key", None)
        host = ""
        if hasattr(llm_config, "complete_url"):
            host = llm_config.complete_url
        elif hasattr(llm_config, "host") and llm_config.host:
            protocol = getattr(llm_config, "protocol", "https")
            port = getattr(llm_config, "port", 443)
            host = f"{protocol}://{llm_config.host}:{port}"
        return {"binding": binding, "model": model, "host": host, "api_key": api_key}

    def _extract_embedding_config(self, embedding_config: t.Any) -> dict[str, t.Any]:
        """Extract embedding configuration from provider-specific config."""
        if isinstance(embedding_config, OpenAICompatEmbeddingsAPI):
            # For OpenAI compatible API, always use hf_model.model_hf_name
            if embedding_config.hf_model is None:
                msg = "OpenAI compatible embeddings API must have hf_model configured"
                raise ValueError(msg)
            model = embedding_config.hf_model.model_hf_name
            host = embedding_config.complete_url
            return {
                "binding": "openai",
                "model": model,
                "api_key": getattr(embedding_config, "api_key", None),
                "dimensions": 1536,  # default for OpenAI
                "host": host,
            }
        if isinstance(embedding_config, OpenAIEmbeddingProvider):
            host = embedding_config.complete_url
            return {
                "binding": "openai",
                "model": embedding_config.model,
                "api_key": embedding_config.api_key,
                "dimensions": 1536,  # default for OpenAI
                "host": host,
            }
        if isinstance(embedding_config, OllamaEmbeddingProvider):
            host = embedding_config.complete_url
            return {
                "binding": "ollama",
                "model": embedding_config.model,
                "api_key": None,
                "dimensions": 1024,  # default for most Ollama embeddings
                "host": host,
            }
        # Fallback to generic extraction
        binding = getattr(embedding_config, "provider", "openai")
        model = getattr(embedding_config, "model", "text-embedding-ada-002")
        api_key = getattr(embedding_config, "api_key", None)

        # Handle dimensions - some providers might not have this
        dimensions = 1536  # default
        if hasattr(embedding_config, "dimensions"):
            dimensions = embedding_config.dimensions

        host = ""
        if hasattr(embedding_config, "complete_url"):
            host = embedding_config.complete_url
        elif hasattr(embedding_config, "host") and embedding_config.host:
            protocol = getattr(embedding_config, "protocol", "https")
            port = getattr(embedding_config, "port", 443)
            host = f"{protocol}://{embedding_config.host}:{port}"

        return {
            "binding": binding,
            "model": model,
            "api_key": api_key,
            "dimensions": dimensions,
            "host": host,
        }

    async def _get_environment_values(
        self, input_: LightRAGAppInputs, app_secrets_name: str
    ) -> dict[str, t.Any]:
        """Configure environment variables for LightRAG."""

        # Extract configurations from provider-specific types
        llm_config = self._extract_llm_config(input_.llm_config)
        embedding_config = self._extract_embedding_config(input_.embedding_config)

        # Build environment configuration matching the full chart structure
        env_config = {
            "HOST": "0.0.0.0",
            "PORT": 9621,
            # Web UI configuration - using default LightRAG values
            "WEBUI_TITLE": "Graph RAG Engine",
            "WEBUI_DESCRIPTION": "Simple and Fast Graph Based RAG System",
            # LLM configuration
            "LLM_BINDING": llm_config["binding"],
            "LLM_MODEL": llm_config["model"],
            "LLM_BINDING_HOST": llm_config["host"],
            "LLM_BINDING_API_KEY": serialize_optional_secret(
                llm_config["api_key"], app_secrets_name
            ),
            "OPENAI_API_KEY": serialize_optional_secret(
                llm_config["api_key"], app_secrets_name
            )
            or "",
            # Embedding configuration
            "EMBEDDING_BINDING": embedding_config["binding"],
            "EMBEDDING_MODEL": embedding_config["model"],
            "EMBEDDING_DIM": embedding_config["dimensions"],
            "EMBEDDING_BINDING_HOST": embedding_config["host"],
            "EMBEDDING_BINDING_API_KEY": serialize_optional_secret(
                embedding_config["api_key"], app_secrets_name
            )
            or "",
            # Storage configuration - hardcoded to match minimal setup
            "LIGHTRAG_KV_STORAGE": "PGKVStorage",
            "LIGHTRAG_VECTOR_STORAGE": "PGVectorStorage",
            "LIGHTRAG_DOC_STATUS_STORAGE": "PGDocStatusStorage",
            "LIGHTRAG_GRAPH_STORAGE": "NetworkXStorage",
            # PostgreSQL connection using Crunchy Postgres app outputs
            "POSTGRES_HOST": input_.pgvector_user.pgbouncer_host,
            "POSTGRES_PORT": input_.pgvector_user.pgbouncer_port,
            "POSTGRES_USER": input_.pgvector_user.user,
            "POSTGRES_PASSWORD": input_.pgvector_user.password,
            "POSTGRES_DATABASE": input_.pgvector_user.dbname,
            "POSTGRES_WORKSPACE": "default",
        }

        # NetworkXStorage uses local file storage, no additional configuration needed

        return {"env": env_config}

    async def _get_persistence_values(
        self, input_: LightRAGAppInputs
    ) -> dict[str, t.Any]:
        """Configure persistence values for LightRAG storage volumes."""
        return {
            "persistence": {
                "enabled": True,
                "ragStorage": {
                    "size": f"{input_.persistence.rag_storage_size}Gi",
                },
                "inputs": {
                    "size": f"{input_.persistence.inputs_storage_size}Gi",
                },
            }
        }

    async def gen_extra_values(
        self,
        input_: LightRAGAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for LightRAG Helm chart deployment."""

        # Get component-specific values
        env_values = await self._get_environment_values(input_, app_secrets_name)
        persistence_values = await self._get_persistence_values(input_)
        # Use gen_extra_values for standard platform values (like LLM app)
        platform_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress_http=input_.ingress_http,
            ingress_grpc=None,
            namespace=namespace,
            app_id=app_id,
            app_type=AppType.LightRAG,
        )

        # Basic chart configuration
        base_values = {
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
                "pullPolicy": "IfNotPresent",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "nameOverride": "",
            "fullnameOverride": app_name,
        }

        logger.debug("Generated LightRAG values for app %s", app_name)

        # Merge all values together
        return merge_list_of_dicts(
            [
                base_values,
                env_values,
                persistence_values,
                platform_values,
            ]
        )
