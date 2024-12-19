from apolo_app_types.common import AppOutputs


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
