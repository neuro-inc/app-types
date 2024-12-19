from pydantic import BaseModel, Field

from apolo_app_types.common import AppOutputs


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
