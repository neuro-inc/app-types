from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import OptionalSecret
from apolo_app_types.protocols.common.storage import ApoloFilesPath


HF_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="Hugging Face Model",
    description="Configure the Hugging Face model. "
    "Ensure it is available on the Hugging Face Hub and provide"
    " an API token with access rights if the repository is gated.",
    meta_type=SchemaMetaType.INTEGRATION,
)
HF_TOKEN_SCHEMA_EXTRA = SchemaExtraMetadata(
    description="Provide a Hugging Face API token linked "
    "to an account with access to the model "
    "specified above. This token will be used to download model"
    " files from the Hugging Face Hub, including "
    "gated or private repositories where applicable.",
    title="Hugging Face Token",
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
    hf_token: OptionalSecret = Field(  # noqa: N815
        default=None,
        json_schema_extra=HF_TOKEN_SCHEMA_EXTRA.as_json_schema_extra(),
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
