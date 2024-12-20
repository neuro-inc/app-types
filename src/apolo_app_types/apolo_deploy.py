from apolo_app_types.common import AppInputs, AppOutputs
from pydantic import field_validator
from yarl import URL

class ApoloDeployInputs(AppInputs):
    preset_name: str
    http_auth: bool = True
    mlflow_tracking_uri: URL | None = None

    @field_validator("mlflow_tracking_uri", mode="before")
    @classmethod
    def mlflow_tracking_uri_validator(cls, raw: str) -> URL:
        return URL(raw)
    

class ApoloDeployOutputs(AppOutputs):
    internal_web_app_url: str
    external_web_app_url: str # type: ignore