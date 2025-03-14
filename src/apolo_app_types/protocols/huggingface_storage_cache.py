from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    ApoloStoragePath,
    AppInputs,
    AppOutputs,
)


class HuggingFaceStorageCacheModel(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "x-title": "HuggingFace Storage Cache Configuration",
            "x-description": "Configuration HF storage.",
            "x-logo-url": "https://example.com/logo",
        }
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
