from pydantic import BaseModel, ConfigDict, Field, field_validator
from yarl import URL

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
    RestAPI,
)
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)


class PrivateGPTInputs(AppInputsDeployer):
    preset_name: str
    llm_inference_app_name: str
    text_embeddings_app_name: str
    pgvector_app_name: str
    http_auth: bool = True
    llm_temperature: float = 0.1
    pgvector_user: str | None = None
    huggingface_token_secret: URL | None = None

    @field_validator("huggingface_token_secret", mode="before")
    @classmethod
    def huggingface_token_secret_validator(cls, raw: str) -> URL:
        return URL(raw)


class PrivateGptSpecific(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="PrivateGPT Specific",
            description="Configure PrivateGPT additional parameters.",
        ).as_json_schema_extra(),
    )
    llm_temperature: float = Field(
        default=0.1,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Temperature",
            description="Configure temperature for LLM inference.",
        ).as_json_schema_extra(),
    )
    embeddings_dimension: int = Field(
        default=768,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Embeddings Dimension",
            description="Configure dimension of embeddings."
            "The number can be found on the Hugging Face model card "
            "or model configuration file.",
        ).as_json_schema_extra(),
    )
    llm_max_new_tokens: int = Field(
        default=5000,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Max New Tokens",
            description="Configure maximum number of new tokens "
            "(limited by GPU memory and model size).",
        ).as_json_schema_extra(),
    )
    llm_context_window: int = Field(
        default=8192,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Context Window",
            description="Configure context window for LLM inference "
            "(defined by model architecture).",
        ).as_json_schema_extra(),
    )
    llm_tokenizer_name: str | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Tokenizer Name",
            description="Configure tokenizer name for LLM inference.",
        ).as_json_schema_extra(),
    )


class PrivateGPTAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp
    pgvector_user: CrunchyPostgresUserCredentials
    embeddings_api: OpenAICompatEmbeddingsAPI
    llm_chat_api: OpenAICompatChatAPI
    private_gpt_specific: PrivateGptSpecific = Field(
        default_factory=lambda: PrivateGptSpecific(),
    )


class PrivateGPTOutputs(AppOutputsDeployer):
    internal_web_app_url: str
    internal_api_url: str
    internal_api_swagger_url: str
    external_api_url: str
    external_api_swagger_url: str
    external_authorization_required: bool


class PrivateGPTAppOutputs(AppOutputs):
    """
    PrivateGPT outputs:
      - internal_web_app_url
      - external_web_app_url
    """

    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
