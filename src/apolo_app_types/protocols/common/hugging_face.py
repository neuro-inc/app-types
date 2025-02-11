from pydantic import BaseModel, Field, SecretStr

from apolo_app_types.protocols.common.secrets import K8sSecret


class HuggingFaceToken(BaseModel):
    value: SecretStr


class HuggingFaceModel(BaseModel):
    modelHFName: str = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )
    modelFiles: str | None = Field(  # noqa: N815
        None, description="The path to the model files.", title="Model Files"
    )
    hfToken: str | K8sSecret | None = Field(  # noqa: N815
        default=None,
        description="The Hugging Face API token.",
        title="Hugging Face Token",
    )
