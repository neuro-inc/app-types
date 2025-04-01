from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


class IngressGrpc(AbstractAppFieldType):
    enabled: bool


class IngressPath(BaseModel):
    path: str = Field(
        default="/",
        title="Path",
        description="Path for the ingress",
    )
    path_type: str = Field(
        default="Prefix",
        title="PathType",
        description="Type of path",
    )
    port_name: str = Field(
        default="http",
        title="PortName",
        description="Port Name",
    )


class Ingress(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Ingress",
            description="Configuration for Ingress.",
        ).as_json_schema_extra(),
    )
    enabled: bool = Field(
        ...,
        description="Indicates whether the ingress is enabled.",
        title="Ingress Enabled",
    )
    clusterName: str = Field(  # noqa: N815
        ...,
        description="The name of the cluster where the ingress is deployed.",
        title="Cluster Name",
    )
    grpc: IngressGrpc | None = Field(default=None, title="Enable GRPC")
    http_auth: bool = Field(
        default=False,
        title="Enable Platform Authentication",
        description="Enable/disable HTTP authentication",
    )
    paths: list[IngressPath] = Field(
        default_factory=lambda: [IngressPath()],
        title="Paths",
        description="Paths for the ingress",
    )
