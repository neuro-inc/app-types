import enum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    Ingress,
    Preset,
    SchemaExtraMetadata,
)


class MLFlowStorageBackend(str, enum.Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class MLFlowSpecificInputs(AppInputs):
    """
    Fields that are MLFlow-specific, such as http_auth,
    storage backend (sqlite/postgres), etc.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow App",
            description="Configuration for MLFlow deployment.",
        ).as_json_schema_extra(),
    )

    # Whether to enable platform-level HTTP auth, if relevant
    http_auth: bool = Field(
        default=True,
        description="Enable platform-level HTTP Basic Authentication?",
        title="HTTP Auth",
    )

    # Let user pick where MLFlow stores metadata
    storage_backend: MLFlowStorageBackend = Field(
        default=MLFlowStorageBackend.SQLITE,
        description="Which storage backend to use for MLFlow.",
        title="Storage Backend",
    )

    # If using Postgres, we might store the name of a Postgres app
    # or other needed info. This is a placeholder:
    postgres_app_name: str | None = Field(
        default=None,
        description="Name of the Postgres platform app (if using POSTGRES).",
        title="Postgres App Name",
    )


class MLFlowAppInputs(AppInputs):
    """
    Parent wrapper that includes the cluster 'preset', 'ingress', and
    the MLFlow-specific fields. This parallels how FooocusAppInputs is structured.
    """

    preset: Preset
    ingress: Ingress
    mlflow_specific: MLFlowSpecificInputs
