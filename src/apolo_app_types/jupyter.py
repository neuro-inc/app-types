from apolo_app_types.common import AppInputs, AppOutputs


class JupyterInputs(AppInputs):
    preset_name: str
    http_auth: bool = True


class JupyterOutputs(AppOutputs):
    internal_web_app_url: str
    external_web_app_url: str
