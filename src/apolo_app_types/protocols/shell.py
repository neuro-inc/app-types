from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer


class ShellInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class ShellOutputs(AppOutputsDeployer):
    internal_web_app_url: str
