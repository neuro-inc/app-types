from typing import Literal

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
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
    host: str = Field(..., description="The host of the HTTP endpoint.")
    port: int = Field(default=80, description="The port of the HTTP endpoint.")
    protocol: str = Field(
        "http", description="The protocol to use, e.g., http or https."
    )
    timeout: float | None = Field(
        default=30.0, description="Connection timeout in seconds."
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
    api_type: Literal["chat"] = "chat"
    endpoint_url: str = "/v1/chat"


class OpenAICompatEmbeddingsAPI(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible Embeddings API",
            description="Configuration for OpenAI compatible embeddings API.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    api_type: Literal["embeddings"] = "embeddings"
    endpoint_url: str = "/v1/embeddings"
