from apolo_app_types.common import AppInputs, AppOutputs


class PycharmInputs(AppInputs):
    preset_name: str
    http_auth: bool = True


class PycharmOutputs(AppOutputs):
    internal_web_app_url: str
    external_web_app_url: str
