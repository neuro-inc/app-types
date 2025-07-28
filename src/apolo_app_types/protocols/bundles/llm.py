from enum import Enum

from pydantic import Field

from apolo_app_types.protocols.common import (
    ApoloSecret,
    AppInputs,
    SchemaExtraMetadata,
)


class Llama4Size(str, Enum):
    scout = "17B-16E"
    scout_instruct = "17B-16E-Instruct"
    maverick = "17B-128E"
    maverick_instruct = "17B-128E-Instruct"
    maverick_fp8 = "17B-128E-Instruct-FP8"


class LLama4Inputs(AppInputs):
    size: Llama4Size
    hf_token: ApoloSecret = Field(  # noqa: N815
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The Hugging Face API token.",
            title="Hugging Face Token",
        ).as_json_schema_extra(),
    )
    autoscaling_enabled: bool = Field(  # noqa: N815
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            description="Enable or disable autoscaling for the LLM.",
            title="Enable Autoscaling",
        ).as_json_schema_extra(),
    )
