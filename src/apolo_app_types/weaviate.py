from apolo_app_types.common import AppOutputs

from pydantic import field


class WeaviateAuth(AppOutputs):
    username: str = ""
    password: str = ""


class WeaviateEndpoints(AppOutputs):
    graphql_endpoint: str | None = field(default=None)
    rest_endpoint: str | None = field(default=None)
    grpc_endpoint: str | None = field(default=None)


class WeaviateOutputs(AppOutputs):
    internal: WeaviateEndpoints = field(default_factory=WeaviateEndpoints)
    external: WeaviateEndpoints | None = field(default=None)
    auth: WeaviateAuth = field(default_factory=WeaviateAuth)
