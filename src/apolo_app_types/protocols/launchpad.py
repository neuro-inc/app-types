import enum

from pydantic import ConfigDict, Field

from apolo_app_types import (
    AppInputs,
    AppOutputs,
    Env,
    HuggingFaceModel,
)
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.networking import (
    HttpApi,
    ServiceAPI,
)
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.common.storage import ApoloFilesPath


class PreConfiguredLLMModels(enum.StrEnum):
    LLAMA_31_8b = "meta-llama/Llama-3.1-8B-Instruct"
    MAGISTRAL_24B = "unsloth/Magistral-Small-2506-GGUF"


class HuggingFaceLLMModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HuggingFace LLM Model",
            description="Specify a custom LLM model to be used in the Launchpad.",
        ).as_json_schema_extra(),
    )
    llm_model: HuggingFaceModel = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Hugging Face Model",
            description="The Hugging Face model to use for the Launchpad.",
        ).as_json_schema_extra(),
    )
    vllm_extra_args: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="VLLM Extra Arguments",
            description="Additional arguments to pass to the VLLM runtime.",
        ).as_json_schema_extra(),
    )


class CustomLLMModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Custom LLM Model",
            description="Specify a custom LLM model to be used in the Launchpad.",
        ).as_json_schema_extra(),
    )
    llm_model_name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Model Name",
            description="The name of the custom LLM model.",
        ).as_json_schema_extra(),
    )
    llm_model_apolo_path: ApoloFilesPath = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Model Path",
            description="Model path within the Apolo Files.",
        ).as_json_schema_extra(),
    )
    vllm_extra_args: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="VLLM Extra Arguments",
            description="Additional arguments to pass to the VLLM runtime.",
        ).as_json_schema_extra(),
    )


class LLMConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Configuration",
            description="Configuration for the LLM model to be used in this Launchpad.",
        ).as_json_schema_extra(),
    )
    llm_model: PreConfiguredLLMModels | HuggingFaceLLMModel | CustomLLMModel = Field(
        default=PreConfiguredLLMModels.LLAMA_31_8b,
        json_schema_extra=SchemaExtraMetadata(
            title="Pre-configured LLM Model",
            description="Select a pre-configured LLM model for the Launchpad.",
        ).as_json_schema_extra(),
    )
    llm_preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Preset",
            description="Preset to use for the LLM model.",
        ).as_json_schema_extra(),
    )
    ui_preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="OpenWebUI Preset",
            description="Preset to use for OpenWebUI.",
        ).as_json_schema_extra(),
    )


class AppsConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apps Configuration",
            description="Configuration for the applications to be launched"
            " in the Launchpad.",
        ).as_json_schema_extra(),
    )
    llm_config: LLMConfig


class LaunchpadConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Launchpad Configuration",
            description="Configuration for the Launchpad application.",
        ).as_json_schema_extra(),
    )
    preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Launchpad Preset",
            description="Preset to use for the Launchpad application.",
        ).as_json_schema_extra(),
    )


class LaunchpadAppInputs(AppInputs):
    launchpad_config: LaunchpadConfig
    apps_config: AppsConfig


class LaunchpadAppOutputs(AppOutputs):
    web_app_url: ServiceAPI[HttpApi] | None = None
