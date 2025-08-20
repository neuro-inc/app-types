from pydantic import BaseModel, ConfigDict, Field, field_validator
from yarl import URL

from apolo_app_types import AppOutputs, OptionalSecret
from apolo_app_types.protocols.common import (
    AppInputs,
    AppInputsDeployer,
    AppOutputsDeployer,
    IngressHttp,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
)


class FooocusInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True
    huggingface_token_secret: URL | None = None

    @field_validator("huggingface_token_secret", mode="before")
    @classmethod
    def huggingface_token_secret_validator(cls, raw: str) -> URL:
        return URL(raw)


class FooocusSpecificAppInputs(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Fooocus App",
            description="Fooocus App configuration.",
        ).as_json_schema_extra(),
    )

    huggingface_token_secret: OptionalSecret = Field(  # noqa: N815
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Token",
            description="Provide the Hugging Face API token"
            " for model access and integration.",
        ).as_json_schema_extra(),
    )


class FooocusAppInputs(AppInputs):
    preset: Preset
    fooocus_specific: FooocusSpecificAppInputs
    ingress_http: IngressHttp


class FooocusAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None


class FooocusOutputs(AppOutputsDeployer):
    internal_web_app_url: str
    external_web_app_url: str
