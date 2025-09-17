from pydantic import Field

from apolo_app_types.protocols.common import AppInputs, AppOutputs, HuggingFaceCache
from apolo_app_types.protocols.common.hugging_face import HuggingFaceToken
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class HuggingFaceAppInputs(AppInputs):
    cache_config: HuggingFaceCache = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Cache",
            description="Configuration for the Hugging Face cache.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra()
    )
    tokens: list[HuggingFaceToken] = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Tokens",
            description="List of Hugging Face API tokens for accessing models.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )


class HuggingFaceAppOutputs(AppOutputs):
    cache_config: HuggingFaceCache
    tokens: list[HuggingFaceToken]
