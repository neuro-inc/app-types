from pydantic import Field

from apolo_app_types.protocols.common import AppInputs, AppOutputs, HuggingFaceCache
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class HuggingFaceCacheInputs(AppInputs):
    cache_config: HuggingFaceCache = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Cache",
            description="Configuration for the Hugging Face cache.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra()
    )


class HuggingFaceCacheOutputs(AppOutputs):
    cache_config: HuggingFaceCache
