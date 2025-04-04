import enum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
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


class MLFlowSpecificInputs(AppInputs):
    """
    MLFlow-specific fields, e.g. whether to use Postgres or SQLite,
    whether to enable platform-level HTTP Auth, etc.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow App",
            description="Configuration for deploying MLFlow.",
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
