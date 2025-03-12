from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    ApoloStoragePath,
    AppInputsV2,
    AppOutputsV2,
    InputType,
)


class HuggingFaceStorageCacheModel(InputType):
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


class HuggingFaceStorageCacheInputs(AppInputsV2):
    storage_cache: HuggingFaceStorageCacheModel


class HuggingFaceStorageCacheOutputs(AppOutputsV2):
    storage_cache: HuggingFaceStorageCacheModel
