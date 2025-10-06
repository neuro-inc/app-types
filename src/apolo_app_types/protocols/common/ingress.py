from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.auth import ApoloAuth, CustomAuth, NoAuth
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


INGRESS_GRPC_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Enable gRPC Ingress",
    description="Enable access to your service over the internet using gRPC.",
)

INGRESS_HTTP_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Enable HTTP Ingress",
    description="Enable access to your application over the internet using HTTPS.",
)


class BaseIngress(AbstractAppFieldType):
    """Base class for ingress configurations with common authentication field."""

    model_config = ConfigDict(protected_namespaces=())

    auth: ApoloAuth | NoAuth | CustomAuth = Field(
        default_factory=ApoloAuth,
        json_schema_extra=SchemaExtraMetadata(
            title="Authentication",
            description=(
                "Configure authentication for this ingress. "
                "Choose Apolo platform authentication, custom middleware, "
                "or no authentication."
            ),
        ).as_json_schema_extra(),
    )


class IngressGrpc(BaseIngress):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=INGRESS_GRPC_SCHEMA_EXTRA.as_json_schema_extra(),
    )


class IngressHttp(BaseIngress):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=INGRESS_HTTP_SCHEMA_EXTRA.as_json_schema_extra(),
    )


class BasicNetworkingConfig(AbstractAppFieldType):
    """Common networking configuration for applications."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Settings",
            description="Configure network access and authentication settings.",
        ).as_json_schema_extra(),
    )
    ingress_http: IngressHttp = Field(
        default_factory=IngressHttp,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Ingress",
            description="Configure HTTP ingress and authentication settings.",
        ).as_json_schema_extra(),
    )
