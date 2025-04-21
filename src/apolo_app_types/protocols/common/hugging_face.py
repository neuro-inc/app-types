from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import OptionalStrOrSecret
from apolo_app_types.protocols.common.storage import ApoloFilesPath


HF_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Hugging Face Model",
    description="Hugging Face Model Configuration.",
    meta_type=SchemaMetaType.INTEGRATION,
)


class HuggingFaceModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=HF_SCHEMA_EXTRA.as_json_schema_extra(),
    )
    model_hf_name: str = Field(  # noqa: N815
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The name of the Hugging Face model.",
            title="Hugging Face Model Name",
        ).as_json_schema_extra(),
    )
    hf_token: OptionalStrOrSecret = Field(  # noqa: N815
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            description="The Hugging Face API token.",
            title="Hugging Face Token",
        ).as_json_schema_extra(),
    )


class HuggingFaceCache(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Cache",
            description="Configuration for the Hugging Face cache.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    files_path: ApoloFilesPath = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The path to the Apolo Files directory where Hugging Face artifacts are cached.",  # noqa: E501
            title="Files Path",
        ).as_json_schema_extra(),
    )
