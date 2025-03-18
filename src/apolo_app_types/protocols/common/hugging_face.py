from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common.secrets_ import OptionalStrOrSecret


class HuggingFaceModel(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
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
