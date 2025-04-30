import enum

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


class MLFlowStorageBackendEnum(str, enum.Enum):
    """Choose which storage backend MLFlow uses."""

    SQLITE = "sqlite"
    POSTGRES = "postgres"


class MLFlowStorageBackendConfig(AbstractAppFieldType):
    """Configuration for the MLFlow storage backend."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Backend",
            description="Which storage backend to use for MLFlow.",
        ).as_json_schema_extra(),
    )
    database: MLFlowStorageBackendEnum = Field(
        default=MLFlowStorageBackendEnum.SQLITE,
        description="Storage backend type (SQLite or Postgres)",
        title="Backend Type",
    )


class SQLitePVCConfig(AbstractAppFieldType):
    """Configuration for the SQLite PVC."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="SQLite PVC",
            description="PVC configuration for SQLite storage.",
        ).as_json_schema_extra(),
    )
    pvc_name: str | None = Field(
        default=None,
        description="Name of the PVC claim to store local DB.",
        title="PVC Name",
    )


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
    pvc_name: str = "mlflow-sqlite-storage"


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
        description=(
            "Use Apolo Files to store your MLFlow artifacts "
            "(model binaries, dependency files, etc). "
            "E.g. 'storage://cluster/myorg/proj/mlflow-artifacts'"
        ),
        title="Artifact Store",
    )


class MLFlowAppOutputs(AppOutputs):
    """
    MLFlow outputs:
      - internal_web_app_url
      - external_web_app_url
    """

    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
