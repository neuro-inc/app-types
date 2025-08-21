from __future__ import annotations

import typing as t
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
from apolo_app_types.protocols.common.schema_extra import SchemaMetaType
from apolo_app_types.protocols.postgres import PostgresURI


class MLFlowMetadataPostgres(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres",
            description="Use PostgreSQL server as metadata storage for MLFlow.",
        ).as_json_schema_extra(),
    )

    storage_type: Literal["postgres"] = Field(
        default="postgres",
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Type",
            description="Storage type for MLFlow metadata.",
        ).as_json_schema_extra(),
    )
    postgres_uri: t.Annotated[
        PostgresURI,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Postgres URI",
                description="Connection URI to the PostgreSQL metadata database.",
            ).as_json_schema_extra()
        ),
    ]


class MLFlowMetadataSQLite(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="SQLite",
            description="Use SQLite on a dedicated block "
            "device as metadata store for MLFlow.",
        ).as_json_schema_extra(),
    )

    storage_type: Literal["sqlite"] = Field(
        default="sqlite",
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Type",
            description="Storage type for MLFlow metadata.",
        ).as_json_schema_extra(),
    )


MLFlowMetaStorage = MLFlowMetadataSQLite | MLFlowMetadataPostgres


class MLFlowAppInputs(AppInputs):
    """
    The overall MLFlow app config, referencing:
      - 'preset' for CPU/GPU resources
      - 'ingress' for external URL
      - 'metadata_storage' for MLFlow settings
      - 'artifact_store' for artifacts location
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Inputs",
            description="Configuration for the MLFlow application.",
        ).as_json_schema_extra(),
    )

    preset: Preset
    ingress_http: IngressHttp
    metadata_storage: MLFlowMetaStorage

    artifact_store: ApoloFilesPath = Field(
        default=ApoloFilesPath(path="storage:mlflow-artifacts"),
        json_schema_extra=SchemaExtraMetadata(
            title="Artifact Store",
            description=(
                "Use Apolo Files to store your MLFlow "
                "artifacts (model binaries, dependency files, etc). "
                "Example absolute path: 'storage://cluster/myorg/"
                "proj/mlflow-artifacts' "
                "or relative path: 'storage:mlflow-artifacts'."
            ),
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


class ModelVersionStatus(StrEnum):
    PENDING_REGISTRATION = "PENDING_REGISTRATION"
    FAILED_REGISTRATION = "FAILED_REGISTRATION"
    READY = "READY"


class ModelVersionTag(BaseModel):
    """Tag metadata for model versions"""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Model Version Tag",
            description="Key-value metadata tag associated with a model version.",
        ).as_json_schema_extra(),
    )

    key: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Tag Key",
                description="Name of the tag.",
            ).as_json_schema_extra()
        ),
    ]
    value: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Tag Value",
                description="Value of the tag.",
            ).as_json_schema_extra()
        ),
    ]


class ModelVersion(BaseModel):
    """Model version information"""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Model Version",
            description="Information about a specific version of a registered model.",
        ).as_json_schema_extra(),
    )

    name: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Name",
                description="Unique name of the model.",
            ).as_json_schema_extra()
        ),
    ]

    version: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Version",
                description="Model's version number.",
            ).as_json_schema_extra()
        ),
    ]

    creation_timestamp: int = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Creation Timestamp",
            description="Timestamp recorded when this model_version was created.",
        ).as_json_schema_extra(),
    )

    last_updated_timestamp: int = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Last Updated Timestamp",
            description="Timestamp recorded when this "
            "model_version metadata was last updated.",
        ).as_json_schema_extra(),
    )

    user_id: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="User ID",
                    description="User that created this model_version.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    current_stage: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Current Stage",
                    description="Current stage for this model"
                    "_version (e.g., Staging, Production).",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    description: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Description",
                    description="Description of this model_version.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    source: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Source",
                    description=(
                        "URI indicating the location of the "
                        "source model artifacts used when creating model_version."
                    ),
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    run_id: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Run ID",
                    description=(
                        "MLflow run ID used when creating model"
                        "_version if source was generated by a run "
                        "stored in an MLflow tracking server."
                    ),
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    status: (
        t.Annotated[
            ModelVersionStatus,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Status",
                    description="Current status of model_version.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    status_message: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Status Message",
                    description="Details on current status,"
                    " if it is pending or failed.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    tags: list[ModelVersionTag] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Tags",
            description="Additional metadata key-value pairs for this model_version.",
        ).as_json_schema_extra(),
    )

    run_link: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Run Link",
                    description=(
                        "Direct link to the run that generated this version. "
                        "Set only when the source run is from a tracking server"
                        " different from the registry server."
                    ),
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    aliases: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Aliases",
            description="Aliases pointing to this model_version.",
        ).as_json_schema_extra(),
    )


class RegisteredModelTag(BaseModel):
    """Tag metadata for registered models"""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Registered Model Tag",
            description="Key-value metadata tag associated with a registered model.",
        ).as_json_schema_extra(),
    )

    key: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Tag Key",
                description="Name of the tag.",
            ).as_json_schema_extra()
        ),
    ]
    value: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Tag Value",
                description="Value of the tag.",
            ).as_json_schema_extra()
        ),
    ]


class RegisteredModelAlias(BaseModel):
    """Alias pointing to model versions"""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Registered Model Alias",
            description="Alias that points to a specific model version.",
        ).as_json_schema_extra(),
    )

    alias: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Alias",
                description="Human-friendly alias (e.g., 'Production').",
            ).as_json_schema_extra()
        ),
    ]
    version: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Version",
                description="Model version that this alias points to.",
            ).as_json_schema_extra()
        ),
    ]


class RegisteredModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Registered Model",
            description="Registered models in MLFlow.",
            meta_type=SchemaMetaType.DYNAMIC,
        ).as_json_schema_extra(),
    )

    name: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Name",
                description="Unique name for the model.",
            ).as_json_schema_extra()
        ),
    ]

    creation_timestamp: int = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Creation Timestamp",
            description="Timestamp recorded when this registered_model was created.",
        ).as_json_schema_extra(),
    )

    last_updated_timestamp: int = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Last Updated Timestamp",
            description="Timestamp recorded when this "
            "registered_model metadata was last updated.",
        ).as_json_schema_extra(),
    )

    user_id: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="User ID",
                    description=(
                        "User that created this registered_model. "
                        "NOTE: this field is not currently returned."
                    ),
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    description: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Description",
                    description="Description of this registered_model.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    latest_versions: list[ModelVersion] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Latest Versions",
            description=(
                "Collection of latest model versions for each stage. "
                "Only contains models with current READY status."
            ),
        ).as_json_schema_extra(),
    )

    tags: list[RegisteredModelTag] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Tags",
            description="Additional metadata key-value"
            " pairs for this registered_model.",
        ).as_json_schema_extra(),
    )

    aliases: list[RegisteredModelAlias] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Aliases",
            description="Aliases pointing to model versions "
            "associated with this registered_model.",
        ).as_json_schema_extra(),
    )


class MLFlowAppOutputs(AppOutputs):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Outputs",
            description="Outputs produced by the MLFlow application.",
        ).as_json_schema_extra(),
    )

    web_app_url: ServiceAPI[HttpApi] = Field(
        default=ServiceAPI[HttpApi](),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Web App URL",
            description="URL to access the MLFlow web application.",
        ).as_json_schema_extra(),
    )

    server_url: MLFlowTrackingServerURL | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Tracking Server URL",
            description="URL to access the MLFlow tracking server.",
        ).as_json_schema_extra(),
    )

    registered_models: list[RegisteredModel] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Registered Models",
            description="List of registered models in MLFlow.",
            meta_type=SchemaMetaType.DYNAMIC,
        ).as_json_schema_extra(),
    )
