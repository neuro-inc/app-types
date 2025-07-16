from typing import Generic, Literal, TypeVar

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
    host: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Hostname", description="The hostname of the HTTP endpoint."
        ).as_json_schema_extra(),
    )
    port: int = Field(
        default=80,
        gt=0,
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

    @property
    def complete_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.base_path}"


class GraphQLAPI(HttpApi):
    api_type: Literal["graphql"] = "graphql"


class RestAPI(HttpApi):
    api_type: Literal["rest"] = "rest"


class GrpcAPI(HttpApi):
    api_type: Literal["grpc"] = "grpc"


API_TYPE = TypeVar("API_TYPE", bound=HttpApi)


class ServiceAPI(AbstractAppFieldType, Generic[API_TYPE]):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Service APIs",
            description="Service APIs URLs.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    internal_url: API_TYPE | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Internal URL",
            description="Internal URL to access the service. "
            "This route is not protected by platform authorization "
            "and only workloads from the same project can access it.",
        ).as_json_schema_extra(),
    )
    external_url: API_TYPE | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External URL",
            description="External URL for accessing the service "
            "from outside the cluster. "
            "This route might be secured by platform "
            "authorization and is accessible from any "
            "network with a valid platform authorization"
            " token that has appropriate permissions.",
        ).as_json_schema_extra(),
    )
