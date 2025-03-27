from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppInputsDeployer,
    AppOutputs,
    AppOutputsDeployer,
    HuggingFaceModel,
    Ingress,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
    SchemaMetaType,
)


class StableStudio(AppInputsDeployer):
    enabled: bool = False
    preset: Preset


class StableDiffusionParams(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Stable Diffusion",
            description="Configuration for Stable Diffusion.",
        ).as_json_schema_extra(),
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


class SDModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Stable Diffusion Model",
            description="Stable Diffusion Model hosted in application.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    name: str
    files: str


class SDOutputs(AppOutputsDeployer):
    internal_api: TextToImgAPI
    external_api: TextToImgAPI
    model: SDModel


class StableDiffusionOutputs(AppOutputs):
    internal_api: RestAPI | None = None
    external_api: RestAPI | None = None
    hf_model: HuggingFaceModel | None = None
