from pydantic import BaseModel, Field

from apolo_app_types.common import AppInputs, AppOutputs, Ingress


class Persistence(BaseModel):
    size: str


class WeaviateClusterApi(BaseModel):
    username: str
    password: str


class WeaviateAuthentication(BaseModel):
    enabled: bool


class WeaviateBackups(BaseModel):
    enabled: bool


class WeaviateInputs(AppInputs):
    preset_name: str
    persistence: Persistence
    ingress: Ingress
    cluster_api: WeaviateClusterApi
    authentication: WeaviateAuthentication
    backups: WeaviateBackups


class WeaviateAuth(BaseModel):
    username: str = ""
    password: str = ""


class WeaviateEndpoints(BaseModel):
    graphql_endpoint: str | None = Field(default=None)
    rest_endpoint: str | None = Field(default=None)
    grpc_endpoint: str | None = Field(default=None)


class WeaviateOutputs(AppOutputs):
    internal: WeaviateEndpoints = Field(default_factory=WeaviateEndpoints)
    external: WeaviateEndpoints | None = Field(default=None)
    auth: WeaviateAuth = Field(default_factory=WeaviateAuth)
