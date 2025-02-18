from pydantic import BaseModel

from apolo_app_types.protocols.common import AppInputs, AppOutputs


class Image(BaseModel):
    repository: str
    tag: str | None = None


class Autoscaling(BaseModel):
    enabled: bool | None = None
    min_replicas: int | None = None
    max_replicas: int | None = None
    target_cpu_utilization_percentage: int | None = None


class Env(BaseModel):
    name: str
    value: str


class Container(BaseModel):
    command: list[str] | None = None
    args: list[str] | None = None
    env: list[Env] | None = None


class CustomDeploymentInputs(AppInputs):
    preset_name: str
    http_auth: bool = True
    name_override: str
    image: Image | None = None
    autoscaling: Autoscaling | None = None
    container: Container | None = None


class CustomDeploymentOutputs(AppOutputs):
    internal_web_app_url: str
