from apolo_app_types.common import AppInputs, AppOutputs

class ShellInputs(AppInputs):
    preset_name: str
    http_auth: bool = True


class ShellOutputs(AppOutputs):
    internal_web_app_url: str
    external_web_app_url: str