from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import SchemaExtraMetadata


class IngressGrpc(BaseModel):
    enabled: bool


class Ingress(BaseModel):
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
    grpc: IngressGrpc | None = None
