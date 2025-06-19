from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppOutputs,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.ingress import (
    INGRESS_HTTP_SCHEMA_EXTRA,
)
from apolo_app_types.protocols.common.networking import HttpApi, ServiceAPI


LIGHTRAG_MIN_GB_STORAGE = 10


class LightRAGPersistence(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LightRAG persistence",
            description=(
                "Configure LightRAG to store data in persistent storage with "
                "PostgreSQL."
            ),
        ).as_json_schema_extra(),
    )

    rag_storage_size: int = Field(
        default=LIGHTRAG_MIN_GB_STORAGE,
        json_schema_extra=SchemaExtraMetadata(
            title="RAG Storage Size (GB)",
            description=("Specify the size of the RAG storage volume in gigabytes."),
        ).as_json_schema_extra(),
    )

    inputs_storage_size: int = Field(
        default=5,
        json_schema_extra=SchemaExtraMetadata(
            title="Inputs Storage Size (GB)",
            description=("Specify the size of the inputs storage volume in gigabytes."),
        ).as_json_schema_extra(),
    )

    postgres_storage_size: int = Field(
        default=LIGHTRAG_MIN_GB_STORAGE,
        json_schema_extra=SchemaExtraMetadata(
            title="PostgreSQL Storage Size (GB)",
            description=(
                "Specify the size of the PostgreSQL storage volume in gigabytes."
            ),
        ).as_json_schema_extra(),
    )

    enable_backups: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Enable backups",
            description=(
                "Enable periodic backups of LightRAG storage to object store. "
                "We automatically create bucket and the corresponding "
                "credentials for you. Note: this bucket will not be "
                "automatically removed when you remove the application."
            ),
        ).as_json_schema_extra(),
    )

    @field_validator(
        "rag_storage_size",
        "inputs_storage_size",
        "postgres_storage_size",
        mode="before",
    )
    def validate_storage_size(cls, value: int) -> int:  # noqa: N805
        if value and isinstance(value, int):
            if value < 1:
                err_msg = "Storage size must be greater than 1GB."
                raise ValueError(err_msg)
        else:
            err_msg = "Storage size must be specified as int."
            raise ValueError(err_msg)
        return value


class LightRAGLLMConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Configuration",
            description="Configure the Language Model for LightRAG processing.",
        ).as_json_schema_extra(),
    )

    binding: Literal["openai", "anthropic", "ollama"] = Field(
        default="openai",
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Provider",
            description="Choose the LLM provider for text generation.",
        ).as_json_schema_extra(),
    )

    model: str = Field(
        default="gpt-4o-mini",
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Model",
            description="Specify the model name to use for text generation.",
        ).as_json_schema_extra(),
    )

    api_key: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="API Key",
            description="API key for the LLM provider. This will be stored securely.",
        ).as_json_schema_extra(),
    )

    host: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Host URL (Optional)",
            description="Custom host URL for self-hosted LLM services (e.g., Ollama).",
        ).as_json_schema_extra(),
    )


class LightRAGEmbeddingConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Configuration",
            description="Configure the embedding model for LightRAG vector processing.",
        ).as_json_schema_extra(),
    )

    binding: Literal["openai", "huggingface", "ollama"] = Field(
        default="openai",
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Provider",
            description="Choose the embedding provider for vector generation.",
        ).as_json_schema_extra(),
    )

    model: str = Field(
        default="text-embedding-ada-002",
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Model",
            description="Specify the embedding model name.",
        ).as_json_schema_extra(),
    )

    dimensions: int = Field(
        default=1536,
        json_schema_extra=SchemaExtraMetadata(
            title="Embedding Dimensions",
            description="Number of dimensions for the embedding vectors.",
        ).as_json_schema_extra(),
    )

    api_key: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="API Key",
            description=(
                "API key for the embedding provider. This will be stored securely."
            ),
        ).as_json_schema_extra(),
    )


class LightRAGWebUIConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Web UI Configuration",
            description="Configure the LightRAG web interface.",
        ).as_json_schema_extra(),
    )

    title: str = Field(
        default="Apolo Copilot - LightRAG",
        json_schema_extra=SchemaExtraMetadata(
            title="UI Title",
            description="Title displayed in the web interface.",
        ).as_json_schema_extra(),
    )

    description: str = Field(
        default="Simple and Fast Graph Based RAG System",
        json_schema_extra=SchemaExtraMetadata(
            title="UI Description",
            description="Description displayed in the web interface.",
        ).as_json_schema_extra(),
    )


class LightRAGInputs(AppInputs):
    preset: Preset
    persistence: LightRAGPersistence
    llm_config: LightRAGLLMConfig
    embedding_config: LightRAGEmbeddingConfig
    webui_config: LightRAGWebUIConfig = Field(default_factory=LightRAGWebUIConfig)
    ingress_http: IngressHttp | None = Field(
        default=None, json_schema_extra=INGRESS_HTTP_SCHEMA_EXTRA.as_json_schema_extra()
    )


class LightRAGOutputs(AppOutputs):
    web_app_url: ServiceAPI[HttpApi] = Field(
        default=ServiceAPI[HttpApi](),
        json_schema_extra=SchemaExtraMetadata(
            title="LightRAG Web App URL",
            description="URL to access the LightRAG web application.",
        ).as_json_schema_extra(),
    )
    server_url: ServiceAPI[HttpApi] = Field(
        default=ServiceAPI[HttpApi](),
        json_schema_extra=SchemaExtraMetadata(
            title="LightRAG Server URL",
            description="URL to access the LightRAG API server.",
        ).as_json_schema_extra(),
    )
