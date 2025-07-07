from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types import (
    AppInputs,
    AppOutputs,
)
from apolo_app_types.protocols.common import (
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.networking import (
    RestAPI,
)
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.postgres import (
    CrunchyPostgresUserCredentials,
)


class OpenWebUISpecific(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenWebUI Specific",
            description="Configure OpenWebUI additional parameters.",
        ).as_json_schema_extra(),
    )
    env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Environment Variables",
            description="List of environment variables to set in"
            " the OpenWebUI application.",
        ).as_json_schema_extra(),
    )


class OpenWebUIAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp
    pgvector_user: CrunchyPostgresUserCredentials
    embeddings_api: OpenAICompatEmbeddingsAPI
    llm_chat_api: OpenAICompatChatAPI
    openwebui_specific: OpenWebUISpecific = Field(
        default_factory=lambda: OpenWebUISpecific(),
    )


class OpenWebUIAppOutputs(AppOutputs):
    """
    OpenWebUI outputs:
      - internal_web_app_url
      - external_web_app_url
    """

    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
