from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apolo_app_types import (
    AppInputs,
    AppOutputs,
    CrunchyPostgresUserCredentials,
)
from apolo_app_types.protocols.common import (
    AppInputsDeployer,
    AppOutputsDeployer,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.networking import (
    HttpApi,
    ServiceAPI,
)


class LightRAGPersistence(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "LightRAG Persistence",
                "x-description": "Configure persistent storage for "
                "LightRAG data and inputs.",
            }
        ).as_json_schema_extra(),
    )

    rag_storage_size: int = Field(
        default=10,
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "RAG Storage Size (GB)",
                "x-description": "Size of the persistent volume for RAG data storage.",
            }
        ).as_json_schema_extra(),
    )

    inputs_storage_size: int = Field(
        default=5,
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Inputs Storage Size (GB)",
                "x-description": "Size of the persistent volume for input files.",
            }
        ).as_json_schema_extra(),
    )

    @field_validator("rag_storage_size", "inputs_storage_size", mode="before")
    @classmethod
    def validate_storage_size(cls, value: int) -> int:
        if value and isinstance(value, int):
            if value < 1:
                error_message = "Storage size must be greater than 1GB."
                raise ValueError(error_message)
        else:
            error_message = "Storage size must be specified as int."
            raise ValueError(error_message)
        return value


class LightRAGLLMConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "LLM Configuration",
                "x-description": "Configure the Language Model for text generation.",
            }
        ).as_json_schema_extra(),
    )

    binding: Literal["openai", "anthropic", "ollama"] = Field(
        default="openai",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "LLM Provider",
                "x-description": "Choose the LLM provider for text generation.",
            }
        ).as_json_schema_extra(),
    )

    model: str = Field(
        default="gpt-4o-mini",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "LLM Model",
                "x-description": "Model name for text generation.",
            }
        ).as_json_schema_extra(),
    )

    api_key: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "API Key",
                "x-description": "API key for the LLM provider (stored securely).",
            }
        ).as_json_schema_extra(),
    )

    host: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Host URL (Optional)",
                "x-description": "Custom host URL for self-hosted services.",
            }
        ).as_json_schema_extra(),
    )


class LightRAGEmbeddingConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Embedding Configuration",
                "x-description": "Configure the embedding model for vector generation.",
            }
        ).as_json_schema_extra(),
    )

    binding: Literal["openai", "huggingface", "ollama"] = Field(
        default="openai",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Embedding Provider",
                "x-description": "Choose the embedding provider.",
            }
        ).as_json_schema_extra(),
    )

    model: str = Field(
        default="text-embedding-ada-002",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Embedding Model",
                "x-description": "Model name for embedding generation.",
            }
        ).as_json_schema_extra(),
    )

    dimensions: int = Field(
        default=1536,
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Embedding Dimensions",
                "x-description": "Number of dimensions for embedding vectors.",
            }
        ).as_json_schema_extra(),
    )

    api_key: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "API Key",
                "x-description": "API key for embedding provider (stored securely).",
            }
        ).as_json_schema_extra(),
    )


class LightRAGWebUIConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Web UI Configuration",
                "x-description": "Configure the LightRAG web interface.",
            }
        ).as_json_schema_extra(),
    )

    title: str = Field(
        default="Apolo Copilot - LightRAG",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "UI Title",
                "x-description": "Title displayed in the web interface.",
            }
        ).as_json_schema_extra(),
    )

    description: str = Field(
        default="Simple and Fast Graph Based RAG System",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "UI Description",
                "x-description": "Description displayed in the web interface.",
            }
        ).as_json_schema_extra(),
    )


class LightRAGStorageConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Storage Configuration",
                "x-description": "Configure LightRAG storage backends.",
            }
        ).as_json_schema_extra(),
    )

    kv_storage: Literal["PGKVStorage", "RedisKVStorage"] = Field(
        default="PGKVStorage",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Key-Value Storage",
                "x-description": "Backend for key-value storage.",
            }
        ).as_json_schema_extra(),
    )

    vector_storage: Literal["PGVectorStorage", "QdrantVectorDBStorage"] = Field(
        default="PGVectorStorage",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Vector Storage",
                "x-description": "Backend for vector storage.",
            }
        ).as_json_schema_extra(),
    )

    graph_storage: Literal["Neo4JStorage", "PGGraphStorage"] = Field(
        default="Neo4JStorage",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Graph Storage",
                "x-description": "Backend for graph storage.",
            }
        ).as_json_schema_extra(),
    )

    doc_status_storage: Literal["PGDocStatusStorage", "RedisDocStatusStorage"] = Field(
        default="PGDocStatusStorage",
        json_schema_extra=SchemaExtraMetadata(
            **{
                "x-title": "Document Status Storage",
                "x-description": "Backend for document processing status.",
            }
        ).as_json_schema_extra(),
    )


# Input classes following PrivateGPT pattern
class LightRAGInputs(AppInputsDeployer):
    preset_name: str
    pgvector_app_name: str
    pgvector_user: str | None = None
    llm_config: LightRAGLLMConfig = Field(default_factory=LightRAGLLMConfig)
    embedding_config: LightRAGEmbeddingConfig = Field(
        default_factory=LightRAGEmbeddingConfig
    )
    webui_config: LightRAGWebUIConfig = Field(default_factory=LightRAGWebUIConfig)
    storage_config: LightRAGStorageConfig = Field(default_factory=LightRAGStorageConfig)
    persistence: LightRAGPersistence = Field(default_factory=LightRAGPersistence)


class LightRAGAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp
    pgvector_user: CrunchyPostgresUserCredentials
    llm_config: LightRAGLLMConfig = Field(default_factory=LightRAGLLMConfig)
    embedding_config: LightRAGEmbeddingConfig = Field(
        default_factory=LightRAGEmbeddingConfig
    )
    webui_config: LightRAGWebUIConfig = Field(default_factory=LightRAGWebUIConfig)
    storage_config: LightRAGStorageConfig = Field(default_factory=LightRAGStorageConfig)
    persistence: LightRAGPersistence = Field(default_factory=LightRAGPersistence)


class LightRAGOutputs(AppOutputsDeployer):
    internal_web_app_url: str
    internal_server_url: str
    external_web_app_url: str
    external_server_url: str
    external_authorization_required: bool


class LightRAGAppOutputs(AppOutputs):
    """
    LightRAG outputs:
      - web_app_url: URL to access the web interface
      - server_url: URL to access the API server
    """

    web_app_url: ServiceAPI[HttpApi] | None = None
    server_url: ServiceAPI[HttpApi] | None = None
