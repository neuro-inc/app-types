from apolo_app_types.common import AppOutputs


class TextToImgAPI(AppOutputs):
    host: str
    port: str | None
    api_base: str

class SDModel(AppOutputs):
    name: str
    files: str


class SDOutputs(AppOutputs):
    internal_api: TextToImgAPI
    external_api: TextToImgAPI
    model: SDModel
    stablestudio_external_web_app_url: str | None = None
    stablestudio_internal_web_app_url: str | None = None
