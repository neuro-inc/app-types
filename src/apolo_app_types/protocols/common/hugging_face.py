import json

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


def serialize_hf_token(value: str | K8sSecret | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, K8sSecret):
        return json.dumps(value.model_dump())
    err_msg = f"Unsupported type for hfToken: {type(value)}"
    raise ValueError(err_msg)
