from apolo_app_types.common import AppInputs, AppOutputs


class VSCodeInputs(AppInputs):
    preset_name: str
    http_auth: bool = True


class VSCodeOutputs(AppOutputs):
    internal_web_app_url: str
