from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


class IngressGrpc(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Enable GRPC Ingress",
            description="Enable access to your service over the internet usingGRPC.",
        ).as_json_schema_extra(),
    )


class IngressHttp(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Enable HTTP Ingress",
            description="Enable access to your "
            "application over the internet using HTTPS.",
        ).as_json_schema_extra(),
    )
    http_auth: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Enable Authentication and Authorization",
            description="Require credentials with "
            "permissions to access this application"
            " for all incoming HTTPS requests.",
        ).as_json_schema_extra(),
    )
