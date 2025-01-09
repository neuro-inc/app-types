from pydantic import BaseModel, Field


class IngressGrpc(BaseModel):
    enabled: bool


class Ingress(BaseModel):
    enabled: str = Field(
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
