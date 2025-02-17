from pydantic import BaseModel, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    AppOutputsV2,
    HuggingFaceModel,
    Ingress,
    Preset,
    RestAPI,
)


class StableStudio(AppInputs):
    enabled: bool = False
    preset: Preset


class StableDiffusionParams(BaseModel):
    replicaCount: int = Field(  # noqa: N815
        default=1,
        description="The number of replicas to deploy.",
        title="Replica Count",
    )
    stablestudio: StableStudio | None = Field(
        default=None,
        description="Stable Studio configuration.",
        title="Stable Studio",
    )
    hugging_face_model: HuggingFaceModel = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )


class StableDiffusionInputs(AppInputs):
    ingress: Ingress
    preset: Preset
    stable_diffusion: StableDiffusionParams  # noqa: N815


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
