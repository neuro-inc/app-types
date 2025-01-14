from apolo_app_types.protocols.common import AppInputs, AppOutputs


class ApoloDeployInputs(AppInputs):
    preset_name: str
    http_auth: bool = True
    mlflow_app_name: str


class ApoloDeployOutputs(AppOutputs):
    internal_web_app_url: str
