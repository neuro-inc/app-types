from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


class IngressGrpc(AbstractAppFieldType):
    enabled: bool = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Enabled",
            description="If GRPC is enabled.",
        ).as_json_schema_extra(),
    )


class Ingress(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Public HTTP Ingress",
            description="Enable access to your "
            "application over the internet using HTTPS.",
        ).as_json_schema_extra(),
    )
    http_auth: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Authorization",
            description="Require credentials with "
            "permissions to access this application"
            " for all incoming HTTPS requests.",
        ).as_json_schema_extra(),
    )
    enabled: bool = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Enable Ingress.",
            title="Ingress Enabled",
        ).as_json_schema_extra(),
    )
    grpc: IngressGrpc | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Enable GRPC",
            description="Enable and configure GRPC support for the ingress.",
        ).as_json_schema_extra(),
    )
