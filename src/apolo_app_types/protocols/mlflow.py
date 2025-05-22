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
from apolo_app_types.protocols.common.networking import HttpApi, ServiceAPI
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


class MLFlowTrackingServerURL(ServiceAPI[RestAPI]):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Server URL",
            description="The URL to access the MLFlow server.",
        ).as_json_schema_extra(),
    )


class MLFlowAppOutputs(AppOutputs):
    web_app_url: ServiceAPI[HttpApi] = Field(
        default=ServiceAPI[HttpApi](),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Web App URL",
            description=("URL to access the MLFlow web application. "),
        ).as_json_schema_extra(),
    )

    server_url: MLFlowTrackingServerURL | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Tracking Server URL",
            description=("URL to access the MLFlow tracking server. "),
        ).as_json_schema_extra(),
    )
