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
    scout = "Scout-17B-16E"
    scout_instruct = "Scout-17B-16E-Instruct"
    maverick_instruct = "Maverick-17B-128E-Instruct"


class DeepSeekR1Size(str, Enum):
    r1 = "R1"
    r1_zero = "R1-Zero"
    r1_distill_llama_70b = "R1-Distill-Llama-70B"
    r1_distill_llama_8b = "R1-Distill-Llama-8B"  # noqa: N815


class MistralSize(str, Enum):
    mistral_7b_v02 = "7B-v0.3"
    mistral_7b_v03 = "7B-v0.2"
    mistral_7b_v01 = "7B-v0.1"
    mistral_31_24b_instruct = "24B-Instruct"


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
