from pydantic import Field

from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer


class MLFlowInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = Field(
        default=True,
        description="Whether to use HTTP basic authentication for the MLFlow web app.",
        title="HTTP authentication",
    )


class MLFlowOutputs(AppOutputsDeployer):
    internal_web_app_url: str
