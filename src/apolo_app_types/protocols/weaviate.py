from pydantic import BaseModel, Field, field_validator

from apolo_app_types.protocols.common import AppInputs, AppOutputs, Ingress, Preset
from apolo_app_types.protocols.common import BasicAuth
from apolo_app_types.protocols.common import GraphQLAPI, GrpcAPI, RestAPI
from apolo_app_types.protocols.common import StorageGB


WEAVIATE_MIN_GB_STORAGE = 32


class WeaviateAuthentication(BaseModel):
    enabled: str = "false"


class WeaviateBackups(BaseModel):
    enabled: bool = False


class WeaviateParams(BaseModel):
    backups: WeaviateBackups = Field(default_factory=WeaviateBackups)
    auth_enabled: bool = False


class WeaviateInputs(AppInputs):
    preset: Preset
    persistence: StorageGB | None = Field(
        default_factory=lambda: StorageGB(size=WEAVIATE_MIN_GB_STORAGE)
    )
    ingress: Ingress | None = None
    clusterApi: BasicAuth | None = None  # noqa: N815
    weaviate_params: WeaviateParams | None = Field(default_factory=WeaviateParams)

    @field_validator("persistence")
    def validate_storage_size(cls, value: StorageGB) -> StorageGB:  # noqa: N805
        if value and isinstance(value.size, int):
            if value.size < WEAVIATE_MIN_GB_STORAGE:
                err_msg = (
                    f"Storage size must be greater than "
                    f"{WEAVIATE_MIN_GB_STORAGE}Gi for Weaviate."
                )
                raise ValueError(err_msg)
        else:
            err_msg = "Storage size must be specified as int."
            raise ValueError(err_msg)
        return value


class WeaviateEndpoints(BaseModel):
    graphql_endpoint: str | None = Field(default=None)
    rest_endpoint: str | None = Field(default=None)
    grpc_endpoint: str | None = Field(default=None)


class WeaviateOutputs(AppOutputs):
    external_graphql_endpoint: GraphQLAPI | None = Field(
        default=None,
        description="The external GraphQL endpoint.",
        title="External GraphQL endpoint",
    )
    external_rest_endpoint: RestAPI | None = Field(
        default=None,
        description="The external REST endpoint.",
        title="External REST endpoint",
    )
    external_grpc_endpoint: GrpcAPI | None = Field(
        default=None,
        description="The external GRPC endpoint.",
        title="External GRPC endpoint",
    )
    internal_graphql_endpoint: GraphQLAPI | None = Field(
        default=None,
        description="The internal GraphQL endpoint.",
        title="Internal GraphQL endpoint",
    )
    internal_rest_endpoint: RestAPI | None = Field(
        default=None,
        description="The internal REST endpoint.",
        title="Internal REST endpoint",
    )
    internal_grpc_endpoint: GrpcAPI | None = Field(
        default=None,
        description="The internal GRPC endpoint.",
        title="Internal GRPC endpoint",
    )
    auth: BasicAuth = Field(default_factory=BasicAuth)
