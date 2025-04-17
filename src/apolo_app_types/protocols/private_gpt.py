from pydantic import BaseModel, ConfigDict, Field, field_validator
from yarl import URL

from apolo_app_types import AppInputs, CrunchyPostgresUserCredentials
from apolo_app_types.protocols.common import (
    AppInputsDeployer,
    AppOutputsDeployer,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.networking import (
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
            description="Configuration for PrivateGPT.",
        ).as_json_schema_extra(),
    )
    llm_temperature: float = 0.1


class PrivateGPTAppInputs(AppInputs):
    preset: Preset
    llm_chat_api: OpenAICompatChatAPI
    pgvector_user: CrunchyPostgresUserCredentials
    tei_api: OpenAICompatEmbeddingsAPI
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
