from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    ApoloStoragePath,
    AppInputs,
    AppOutputs,
    SchemaExtraMetadata,
)


class HuggingFaceStorageCacheModel(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HuggingFace Storage Cache",
            description="Configuration for HuggingFace storage cache.",
        ).as_json_schema_extra(),
    )
    storage_path: ApoloStoragePath = Field(
        ...,
        description="The path to the Apolo Storage where HuggingFace artifacts are cached.",  # noqa: E501
        title="Storage path",
    )


class HuggingFaceStorageCacheInputs(AppInputs):
    storage_cache: HuggingFaceStorageCacheModel


class HuggingFaceStorageCacheOutputs(AppOutputs):
    storage_cache: HuggingFaceStorageCacheModel
