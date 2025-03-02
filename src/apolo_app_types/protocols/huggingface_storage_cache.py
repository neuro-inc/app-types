from pydantic import BaseModel, Field

from apolo_app_types.protocols.common import ApoloStoragePath, AppInputsV2, AppOutputsV2


class HuggingFaceStorageCacheModel(BaseModel):
    storage_path: ApoloStoragePath = Field(
        ...,
        description="The path to the Apolo Storage where HuggingFace artifacts are cached.",  # noqa: E501
        title="Storage path",
    )


class HuggingFaceStorageCacheInputs(AppInputsV2):
    storage_cache: HuggingFaceStorageCacheModel


class HuggingFaceStorageCacheOutputs(AppOutputsV2):
    storage_cache: HuggingFaceStorageCacheModel
