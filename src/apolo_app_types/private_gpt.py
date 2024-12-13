from pydantic import field_validator
from yarl import URL

from apolo_app_types.common import AppInputs, AppOutputs


class PrivateGPTInputs(AppInputs):
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


class PrivateGPTOutputs(AppOutputs):
    internal_web_app_url: str
    internal_api_url: str
    internal_api_swagger_url: str
    external_web_app_url: str
    external_api_url: str
    external_api_swagger_url: str
    external_authorization_required: bool
