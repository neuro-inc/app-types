import enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apolo_app_types import (
    AppInputs,
    AppOutputs,
)
from apolo_app_types.protocols.common import (
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.networking import (
    HttpApi,
    ServiceAPI,
)
from apolo_app_types.protocols.common.secrets_ import OptionalStrOrSecret
from apolo_app_types.protocols.postgres import CrunchyPostgresUserCredentials


class LightRAGPersistence(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LightRAG Persistence",
            description="Configure persistent storage for LightRAG data and inputs.",
        ).as_json_schema_extra(),
    )

    rag_storage_size: int = Field(
        default=10,
        json_schema_extra=SchemaExtraMetadata(
            title="RAG Storage Size (GB)",
            description="Size of the persistent volume for RAG data storage.",
        ).as_json_schema_extra(),
    )

    inputs_storage_size: int = Field(
        default=5,
        json_schema_extra=SchemaExtraMetadata(
            title="Inputs Storage Size (GB)",
            description="Size of the persistent volume for input files.",
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


class LLMProviders(enum.StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    VLLM = "vllm"


class LightRAGLLMConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Configuration",
            description="Configure the Language Model for text generation.",
        ).as_json_schema_extra(),
    )

    binding: LLMProviders = Field(
        default=LLMProviders.OPENAI,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Provider",
            description="Choose the LLM provider for text generation.",
        ).as_json_schema_extra(),
    )

    model: str = Field(
        default="gpt-4o-mini",
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Model",
            description="Model name for text generation.",
        ).as_json_schema_extra(),
    )

    api_key: OptionalStrOrSecret = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="API Key",
            description="API key for the LLM provider (stored securely).",
        ).as_json_schema_extra(),
    )

    host: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Host URL (Optional)",
            description="Custom host URL for self-hosted services.",
        ).as_json_schema_extra(),
    )


class LightRAGEmbeddingConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Configuration",
            description="Configure the embedding model for vector generation.",
        ).as_json_schema_extra(),
    )

    binding: LLMProviders = Field(
        default=LLMProviders.OPENAI,
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Provider",
            description="Choose the embedding provider.",
        ).as_json_schema_extra(),
    )

    model: str = Field(
        default="text-embedding-ada-002",
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Model",
            description="Model name for embedding generation.",
        ).as_json_schema_extra(),
    )

    dimensions: int = Field(
        default=1536,
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Dimensions",
            description="Number of dimensions for embedding vectors.",
        ).as_json_schema_extra(),
    )

    api_key: OptionalStrOrSecret = Field(  # noqa: N815
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="API Key",
            description="API key for embedding provider (stored securely).",
        ).as_json_schema_extra(),
    )


class LightRAGAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp
    pgvector_user: CrunchyPostgresUserCredentials
    llm_config: LightRAGLLMConfig = Field(default_factory=LightRAGLLMConfig)
    embedding_config: LightRAGEmbeddingConfig = Field(
        default_factory=LightRAGEmbeddingConfig
    )
    persistence: LightRAGPersistence = Field(default_factory=LightRAGPersistence)


class LightRAGAppOutputs(AppOutputs):
    """
    LightRAG outputs:
      - web_app_url: URL to access the web interface
      - server_url: URL to access the API server
    """

    web_app_url: ServiceAPI[HttpApi] | None = None
    server_url: ServiceAPI[HttpApi] | None = None
