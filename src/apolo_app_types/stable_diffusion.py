from apolo_app_types.common import AppInputs, AppOutputs, HuggingFaceModel


class SDIngress(AppInputs):
    enabled: bool


class SDAPI(AppInputs):
    replicaCount: int
    ingress: AppInputs


class StableStudio(AppInputs):
    enabled: bool
    preset_name: str


class SDInputs(AppInputs):
    api: SDAPI
    stablestudio: AppInputs
    model: HuggingFaceModel


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
