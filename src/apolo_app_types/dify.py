from apolo_app_types.common import AppOutputs


class DifyOutputs(AppOutputs):
    internal_web_app_url: str
    internal_api_url: str
    external_api_url: str | None
    init_password: str
