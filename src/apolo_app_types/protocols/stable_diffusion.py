from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppInputsDeployer,
    AppOutputs,
    AppOutputsDeployer,
    HuggingFaceModel,
    Ingress,
    Preset,
    RestAPI,
)


class StableStudio(AppInputsDeployer):
    enabled: bool = False
    preset: Preset


class StableDiffusionParams(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "title": "Stable Diffusion Configuration",
            "description": "Configuration for Stable Diffusion.",
            "x-logo-url": "https://example.com/logo",
        },
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


class StableDiffusionInputs(AppInputs):
    ingress: Ingress
    preset: Preset
    stable_diffusion: StableDiffusionParams


class TextToImgAPI(AppOutputsDeployer):
    host: str
    port: str | None
    api_base: str

    @property
    def endpoint_url(self) -> str:
        return self.api_base + "/txt2img"


class SDModel(BaseModel):
    name: str
    files: str


class SDOutputs(AppOutputsDeployer):
    internal_api: TextToImgAPI
    external_api: TextToImgAPI
    model: SDModel


class SDOutputsV2(AppOutputs):
    internal_api: RestAPI | None = None
    external_api: RestAPI | None = None
    hf_model: HuggingFaceModel | None = None
