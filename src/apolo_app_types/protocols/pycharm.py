from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer


class PycharmInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class PycharmOutputs(AppOutputsDeployer):
    internal_web_app_url: str
