from pydantic import ConfigDict, Field, field_validator

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppOutputs,
    BasicAuth,
    GraphQLAPI,
    GrpcAPI,
    IngressHttp,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.ingress import (
    INGRESS_HTTP_SCHEMA_EXTRA,
)


WEAVIATE_MIN_GB_STORAGE = 32


class WeaviatePersistence(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Weaviate persistence",
            description=("Configure Weaviate to store data in a persistent storage."),
        ).as_json_schema_extra(),
    )
    size: int = Field(
        default=WEAVIATE_MIN_GB_STORAGE,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Size (GB)",
            description="Specify the size of the storage volume in gigabytes.",
        ).as_json_schema_extra(),
    )
    enable_backups: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Enable backups",
            description=(
                "Enable periodic backups of Weaviate storage to object store. "
                "We automatically create bucket and the corresponding "
                "credentials for you. Note: this bucket will not be "
                "automatically removed when you remove the bucket."
            ),
        ).as_json_schema_extra(),
    )

    @field_validator("size", mode="before")
    def validate_storage_size(cls, value: int) -> int:  # noqa: N805
        if value and isinstance(value, int):
            if value < WEAVIATE_MIN_GB_STORAGE:
                err_msg = (
                    f"Storage size must be greater than "
                    f"{WEAVIATE_MIN_GB_STORAGE}Gi for Weaviate."
                )
                raise ValueError(err_msg)
        else:
            err_msg = "Storage size must be specified as int."
            raise ValueError(err_msg)
        return value


class WeaviateInputs(AppInputs):
    preset: Preset
    persistence: WeaviatePersistence
    ingress_http: IngressHttp | None = Field(
        default=None, json_schema_extra=INGRESS_HTTP_SCHEMA_EXTRA.as_json_schema_extra()
    )
    ## TODO: add this back when we make it work with platform auth
    # ingress_grpc: IngressGrpc | None = Field(
    #     default=None,
    #     json_schema_extra=INGRESS_GRPC_SCHEMA_EXTRA.as_json_schema_extra()
    # )


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
    ## TODO: add this back when we make it work with platform auth
    # external_grpc_endpoint: GrpcAPI | None = Field(
    #     default=None,
    #     description="The external GRPC endpoint.",
    #     title="External GRPC endpoint",
    # )
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
