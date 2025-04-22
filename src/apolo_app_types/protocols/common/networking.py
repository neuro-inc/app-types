from typing import Literal

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.hugging_face import (
    HF_SCHEMA_EXTRA,
    HuggingFaceModel,
)
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class HttpApi(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP API",
            description="HTTP API Configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    host: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Hostname", description="The hostname of the HTTP endpoint."
        ).as_json_schema_extra(),
    )
    port: int = Field(
        default=80,
        json_schema_extra=SchemaExtraMetadata(
            title="Port", description="The port of the HTTP endpoint."
        ).as_json_schema_extra(),
    )
    protocol: str = Field(
        "http",
        json_schema_extra=SchemaExtraMetadata(
            title="Protocol", description="The protocol to use, e.g., http or https."
        ).as_json_schema_extra(),
    )
    timeout: float | None = Field(
        default=30.0,
        json_schema_extra=SchemaExtraMetadata(
            description="Connection timeout in seconds.",
            title="Connection Timeout",
        ).as_json_schema_extra(),
    )
    base_path: str = "/"

    def get_api_base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.base_path}"


class GraphQLAPI(HttpApi):
    api_type: Literal["graphql"] = "graphql"


class RestAPI(HttpApi):
    api_type: Literal["rest"] = "rest"


class GrpcAPI(HttpApi):
    api_type: Literal["grpc"] = "grpc"


class OpenAICompatChatAPI(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible Chat API",
            description="Configuration for OpenAI compatible chat API.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    # used to distinguish between different types of APIs (chat, embeddings, etc)
    api_type: Literal["chat"] = "chat"
    endpoint_url: Literal["/v1/chat"] = "/v1/chat"
    hf_model: HuggingFaceModel | None = Field(
        default=None,
        json_schema_extra=HF_SCHEMA_EXTRA.as_json_schema_extra(),
    )


class OpenAICompatEmbeddingsAPI(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible Embeddings API",
            description="Configuration for OpenAI compatible embeddings API.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    # used to distinguish between different types of APIs (chat, embeddings, etc)
    api_type: Literal["embeddings"] = "embeddings"
    endpoint_url: Literal["/v1/embeddings"] = "/v1/embeddings"
    hf_model: HuggingFaceModel | None = Field(
        default=None,
        json_schema_extra=HF_SCHEMA_EXTRA.as_json_schema_extra(),
    )
