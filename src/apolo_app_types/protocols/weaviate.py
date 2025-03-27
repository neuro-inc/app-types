from pydantic import Field, field_validator

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AppOutputs,
    BasicAuth,
    Bucket,
    GraphQLAPI,
    GrpcAPI,
    Ingress,
    Preset,
    RestAPI,
    StorageGB,
)


WEAVIATE_MIN_GB_STORAGE = 32


class WeaviateInputs(AppInputs):
    preset: Preset
    persistence: StorageGB = Field(
        default_factory=lambda: StorageGB(size=WEAVIATE_MIN_GB_STORAGE)
    )
    backup_bucket: Bucket | None = None
    ingress: Ingress
    cluster_api: BasicAuth | None = None  # noqa: N815

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
