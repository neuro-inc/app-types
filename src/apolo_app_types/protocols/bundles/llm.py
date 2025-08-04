import typing
from enum import Enum
from typing import Literal

from pydantic import Field

from apolo_app_types.protocols.common import (
    ApoloSecret,
    AppInputs,
    Preset,
    SchemaExtraMetadata,
)


TSize = typing.TypeVar("TSize")


class Llama4Size(str, Enum):
    scout = "17B-16E"
    scout_instruct = "17B-16E-Instruct"
    maverick = "17B-128E"
    maverick_instruct = "17B-128E-Instruct"
    maverick_fp8 = "17B-128E-Instruct-FP8"


class DeepSeekR1Size(str, Enum):
    r1_7b = "7B"
    r1_70b = "70B"
    r1_70b_instruct = "70B-Instruct"
    r1_70b_fp8 = "70B-FP8"


class MistralSize(str, Enum):
    mistral_7b = "7B"
    mistral_7b_instruct = "7B-Instruct"
    mistral_7b_fp8 = "7B-FP8"
    mistral_15b = "15B"
    mistral_15b_instruct = "15B-Instruct"
    mistral_15b_fp8 = "15B-FP8"


class LLMBundleInputs(AppInputs, typing.Generic[TSize]):
    """
    Base class for LLM bundle inputs.
    This class can be extended by specific LLM bundle input classes.
    """

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

    preset: Preset | None = None
    size: TSize


class LLama4Inputs(LLMBundleInputs[Llama4Size]):
    """
    Inputs for the Llama4 bundle.
    This class extends LLMBundleInputs to include specific fields for Llama4.
    """

    size: Llama4Size
    llm_class: Literal["llama4"] = "llama4"


class DeepSeekR1Inputs(LLMBundleInputs[DeepSeekR1Size]):
    """
    Inputs for the DeepSeekR1 bundle.
    This class extends LLMBundleInputs to include specific fields for DeepSeekR1.
    """

    llm_class: Literal["deepseek_r1"] = "deepseek_r1"
    size: DeepSeekR1Size


class MistralInputs(LLMBundleInputs[MistralSize]):
    """
    Inputs for the Mistral bundle.
    This class extends LLMBundleInputs to include specific fields for Mistral.
    """

    llm_class: Literal["mistral"] = "mistral"
    size: MistralSize
