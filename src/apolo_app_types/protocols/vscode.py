from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer


class VSCodeInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class VSCodeOutputs(AppOutputsDeployer):
    internal_web_app_url: str
