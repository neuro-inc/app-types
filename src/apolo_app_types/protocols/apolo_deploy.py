from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer


class ApoloDeployInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True
    mlflow_app_name: str


class ApoloDeployOutputs(AppOutputsDeployer):
    internal_web_app_url: str
