from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import OptionalStrOrSecret
from apolo_app_types.protocols.common.storage import ApoloFilesPath


class HuggingFaceModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Model",
            description="Hugging Face Model Configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    model_hf_name: str = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )
    model_files: str | None = Field(  # noqa: N815
        None, description="The path to the model files.", title="Model Files"
    )
    hf_token: OptionalStrOrSecret = Field(  # noqa: N815
        default=None,
        description="The Hugging Face API token.",
        title="Hugging Face Token",
    )


class HuggingFaceCache(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HuggingFace Cache",
            description="Configuration for HuggingFace cache.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    storage_path: ApoloFilesPath = Field(
        ...,
        description="The path to the Apolo Files where HuggingFace artifacts are cached.",  # noqa: E501
        title="Storage path",
    )
