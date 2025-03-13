from pydantic import BaseModel, ConfigDict, Field


class IngressGrpc(BaseModel):
    enabled: bool


class Ingress(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "x-title": "Ingress Configuration",
            "x-description": "Configuration for Ingress.",
            "x-logo-url": "https://example.com/logo",
        }
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
