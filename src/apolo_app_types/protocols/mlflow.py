import enum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    ApoloFilesPath,
    AppInputs,
    Ingress,
    Preset,
    SchemaExtraMetadata,
)


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
    backend: MLFlowStorageBackendEnum = Field(
        default=MLFlowStorageBackendEnum.SQLITE,
        description="Storage backend type (SQLite or Postgres)",
        title="Backend Type",
    )


class PostgresAppNameConfig(AbstractAppFieldType):
    """Configuration for the Postgres app name."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres App Name",
            description="Name of a Postgres app if using POSTGRES.",
        ).as_json_schema_extra(),
    )
    name: str | None = Field(
        default=None,
        description="The name of the Postgres application.",
        title="App Name",
    )


class HttpAuthConfig(AbstractAppFieldType):
    """Configuration for HTTP authentication."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Auth",
            description="HTTP authentication configuration",
        ).as_json_schema_extra(),
    )
    enabled: bool = Field(
        default=True,
        description="Enable platform-level HTTP Basic Authentication?",
        title="HTTP Auth",
    )


class PostgresURIConfig(AbstractAppFieldType):
    """Configuration for the Postgres connection URI."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres URI",
            description="Full Postgres connection URI configuration.",
        ).as_json_schema_extra(),
    )
    uri: str | None = Field(
        default=None,
        description=(
            "Full Postgres connection URI if using 'postgres'. "
            "E.g. 'postgresql://user:pass@host:5432/db'"
        ),
        title="URI",
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


class ArtifactStoreConfig(AbstractAppFieldType):
    """Configuration for MLFlow artifact storage."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Artifact Store",
            description="Configuration for MLFlow artifact storage.",
        ).as_json_schema_extra(),
    )
    path: ApoloFilesPath | None = Field(
        default=None,
        description=(
            "Path to Apolo Files for MLFlow artifacts. "
            "E.g. 'storage://cluster/myorg/proj/mlflow-artifacts'"
        ),
        title="Storage Path",
    )


class MLFlowSpecificInputs(AppInputs):
    """MLFlow-specific configuration fields."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow App",
            description=(
                "Configuration for deploying MLFlow with a local or Postgres DB, "
                "plus artifacts on Apolo Files."
            ),
        ).as_json_schema_extra(),
    )

    http_auth: HttpAuthConfig = Field(
        default_factory=HttpAuthConfig,
        description="HTTP authentication configuration",
        title="HTTP Auth",
    )

    storage_backend: MLFlowStorageBackendConfig = Field(
        default_factory=MLFlowStorageBackendConfig,
        description="MLFlow storage backend configuration",
        title="Storage Backend",
    )

    postgres_app_name: PostgresAppNameConfig | None = Field(
        default=None,
        description="Postgres application name configuration (if using POSTGRES)",
        title="Postgres App Name",
    )

    postgres_uri: PostgresURIConfig | None = Field(
        default=None,
        description="Postgres connection URI configuration",
        title="Postgres URI",
    )

    sqlite_pvc: SQLitePVCConfig | None = Field(
        default=None,
        description="SQLite PVC configuration",
        title="SQLite PVC",
    )

    artifact_store: ArtifactStoreConfig | None = Field(
        default=None,
        description="Artifact store configuration",
        title="Artifact Store",
    )


class MLFlowAppInputs(AppInputs):
    """
    The overall MLFlow app config, referencing:
      - 'preset' for CPU/GPU resources
      - 'ingress' for external URL
      - 'mlflow_specific' for MLFlow settings
    """

    preset: Preset
    ingress: Ingress
    mlflow_specific: MLFlowSpecificInputs
