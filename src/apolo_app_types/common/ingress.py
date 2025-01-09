from pydantic import BaseModel, Field


class IngressGrpc(BaseModel):
    enabled: bool


class Ingress(BaseModel):
    enabled: str = Field(
        ...,  # Required field
        description="Indicates whether the ingress is enabled. Acceptable values are 'true' or 'false'.",
        title="Ingress Enabled"
    )
    clusterName: str = Field(
        ...,  # Required field
        description="The name of the cluster where the ingress is deployed.",
        title="Cluster Name"
    )
    grpc: IngressGrpc | None = None
