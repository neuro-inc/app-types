from pydantic import Field
from typing_extensions import deprecated

from apolo_app_types.protocols.common import AppInputs, AppOutputs, HuggingFaceCache
from apolo_app_types.protocols.common.hugging_face import (
    HF_TOKEN_SCHEMA_EXTRA,
    HuggingFaceToken,
)
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
    token: HuggingFaceToken = Field(
        ...,
        json_schema_extra=HF_TOKEN_SCHEMA_EXTRA.model_copy(
            update={
                "meta_type": SchemaMetaType.INLINE,
            }
        ).as_json_schema_extra(),
    )


class HuggingFaceAppOutputs(AppOutputs):
    cache_config: HuggingFaceCache
    token: HuggingFaceToken


@deprecated("HuggingFaceCacheInputs is deprecated; use HuggingFaceAppInputs.")
class HuggingFaceCacheInputs(AppInputs):
    cache_config: HuggingFaceCache = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Cache",
            description="Configuration for the Hugging Face cache.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra()
    )


@deprecated("HuggingFaceCacheOutputs is deprecated; use HuggingFaceAppOutputs.")
class HuggingFaceCacheOutputs(AppOutputs):
    cache_config: HuggingFaceCache
