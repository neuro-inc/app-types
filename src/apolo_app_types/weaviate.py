from pydantic import BaseModel, Field

from apolo_app_types.common import AppInputs, AppOutputs, Ingress, Preset


class Persistence(BaseModel):
    size: str


class WeaviateClusterApi(BaseModel):
    username: str
    password: str


class WeaviateAuthentication(BaseModel):
    enabled: str = "false"


class WeaviateBackups(BaseModel):
    enabled: bool


class WeaviateInputs(AppInputs):
    preset: Preset
    persistence: Persistence | None = None
    ingress: Ingress | None = None
    clusterApi: WeaviateClusterApi | None = None  # noqa: N815
    authentication: WeaviateAuthentication | None = None
    backups: WeaviateBackups | None = None


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
