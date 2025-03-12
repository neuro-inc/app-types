from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppInputsV2,
    AppOutputs,
    AppOutputsV2,
    HuggingFaceModel,
    Ingress,
    InputType,
    Preset,
    RestAPI,
)


class StableStudio(AppInputs):
    enabled: bool = False
    preset: Preset


class StableDiffusionParams(InputType):
    model_config = InputType.model_config | ConfigDict(
        json_schema_extra={
            "x-title": "LLM Configuration",
            "x-description": "Configuration for LLM.",
            "x-logo-url": "https://example.com/logo",
        }
    )
    replica_count: int = Field(
        default=1,
        description="The number of replicas to deploy.",
        title="Replica Count",
    )
    hugging_face_model: HuggingFaceModel = Field(
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )


class StableDiffusionInputs(AppInputsV2):
    ingress: Ingress
    preset: Preset
    stable_diffusion: StableDiffusionParams


class TextToImgAPI(AppOutputs):
    host: str
    port: str | None
    api_base: str

    @property
    def endpoint_url(self) -> str:
        return self.api_base + "/txt2img"


class SDModel(AppOutputs):
    name: str
    files: str


class SDOutputs(AppOutputs):
    internal_api: TextToImgAPI
    external_api: TextToImgAPI
    model: SDModel
    internal_web_app_url: str | None = None


class SDOutputsV2(AppOutputsV2):
    internal_api: RestAPI | None = None
    external_api: RestAPI | None = None
    hf_model: HuggingFaceModel | None = None
