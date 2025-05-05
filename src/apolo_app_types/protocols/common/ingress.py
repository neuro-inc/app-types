from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


INGRESS_GRPC_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Enable gRPC Ingress",
    description="Enable access to your service over the internet using gRPC.",
)

INGRESS_HTTP_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Enable HTTP Ingress",
    description="Enable access to your application over the internet using HTTPS.",
)


class IngressGrpc(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=INGRESS_GRPC_SCHEMA_EXTRA.as_json_schema_extra(),
    )
    auth: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Enable Authentication and Authorization",
            description="Require authenticated credentials with appropriate "
            "permissions for all incoming gRPC requests "
            "to the application.",
        ).as_json_schema_extra(),
    )


class IngressHttp(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=INGRESS_HTTP_SCHEMA_EXTRA.as_json_schema_extra(),
    )
    auth: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Enable Authentication and Authorization",
            description="Require authenticated user credentials"
            " with appropriate permissions "
            "for all incoming HTTPS requests to the application.",
        ).as_json_schema_extra(),
    )
