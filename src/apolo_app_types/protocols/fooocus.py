from pydantic import field_validator
from yarl import URL

from apolo_app_types.protocols.common import AppOutputs, AppInputs


class FooocusInputs(AppInputs):
    preset_name: str
    http_auth: bool = True
    huggingface_token_secret: URL | None = None

    @field_validator("huggingface_token_secret", mode="before")
    @classmethod
    def huggingface_token_secret_validator(cls, raw: str) -> URL:
        return URL(raw)


class FooocusOutputs(AppOutputs):
    internal_web_app_url: str
    external_web_app_url: str
