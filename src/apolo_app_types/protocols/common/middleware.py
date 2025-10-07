from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class IngressMiddleware(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Ingress Middleware",
            description="Configure middleware for ingress traffic.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Middleware Name",
            description="Name of the middleware to apply to ingress traffic.",
        ).as_json_schema_extra(),
    )


class AuthIngressMiddleware(IngressMiddleware):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Authentication Ingress Middleware",
            description="Configure authentication middleware for ingress traffic.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    name: str = Field(
        ...,
        pattern=r"^platform",
        json_schema_extra=SchemaExtraMetadata(
            title="Middleware Name",
            description="Name of the authentication middleware (with namespace) to"
            " apply to ingress traffic.",
        ).as_json_schema_extra(),
    )
