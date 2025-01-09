from pydantic import Field
from apolo_app_types.common import AppInputs, AppOutputs, Preset


class MLFlowInputs(AppInputs):
    preset: Preset
    http_auth: bool = Field(
        default=True,
        description="Whether to use HTTP basic authentication for the MLFlow web app.",
        title="HTTP authentication"
    )



class MLFlowOutputs(AppOutputs):
    internal_web_app_url: str
