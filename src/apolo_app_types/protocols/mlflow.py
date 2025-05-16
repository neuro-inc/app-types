from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    ApoloFilesPath,
    AppInputs,
    AppOutputs,
    IngressHttp,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.postgres import PostgresURI


class MLFlowMetadataPostgres(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres",
            description="Use PostgreSQL server as metadata storage for MLFlow.",
        ).as_json_schema_extra(),
    )
    postgres_uri: PostgresURI


class MLFlowMetadataSQLite(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="SQLite",
            description=(
                "Use SQLite on a dedicated block device as metadata store for MLFlow."
            ),
        ).as_json_schema_extra(),
    )
    pvc_name: str = Field(
        default="mlflow-sqlite-storage",
        json_schema_extra=SchemaExtraMetadata(
            description="Specify the name of the PVC claim to store local DB.",
            title="PVC Name",
        ).as_json_schema_extra(),
    )


MLFlowMetaStorage = MLFlowMetadataSQLite | MLFlowMetadataPostgres


class MLFlowAppInputs(AppInputs):
    """
    The overall MLFlow app config, referencing:
      - 'preset' for CPU/GPU resources
      - 'ingress' for external URL
      - 'mlflow_specific' for MLFlow settings
    """

    preset: Preset
    ingress_http: IngressHttp
    metadata_storage: MLFlowMetaStorage
    artifact_store: ApoloFilesPath = Field(
        default=ApoloFilesPath(path="storage:mlflow-artifacts"),
        json_schema_extra=SchemaExtraMetadata(
            description=(
                "Use Apolo Files to store your MLFlow artifacts "
                "(model binaries, dependency files, etc). "
                "E.g. 'storage://cluster/myorg/proj/mlflow-artifacts'"
                "or relative path E.g. 'storage:mlflow-artifacts'"
            ),
            title="Artifact Store",
        ).as_json_schema_extra(),
    )


class MLFlowAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Internal MLFlow URL",
            description=(
                "Internal URL to access the MLFlow web "
                "app and API from inside the cluster. "
                "This route is not protected by platform authorization "
                "and only workloads from the same project can access it."
            ),
        ).as_json_schema_extra(),
    )
    external_web_app_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External MLFlow URL",
            description=(
                "External URL for accessing the MLFlow web "
                "application and API from outside the cluster. "
                "This route is secured by platform "
                "authorization and is accessible from any "
                "network with a valid platform authorization"
                " token that has appropriate permissions."
            ),
        ).as_json_schema_extra(),
    )
