from typing import Any

from apolo_app_types.protocols.common import Protocol
from pydantic import Field

from apolo_app_types.protocols.common.secrets_ import K8sSecret, OptionalStrOrSecret


class HuggingFaceModel(Protocol):
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


def serialize_hf_token(value: str | K8sSecret | None) -> dict[str, Any] | str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, K8sSecret):
        return value.model_dump()
    err_msg = f"Unsupported type for hfToken: {type(value)}"
    raise ValueError(err_msg)
