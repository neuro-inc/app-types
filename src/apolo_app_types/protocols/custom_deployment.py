from pydantic import BaseModel, Field

from apolo_app_types.protocols.common import AppInputsV2, AppOutputsV2, Preset, RestAPI
from apolo_app_types.protocols.common.ingress import Ingress


class ContainerImage(BaseModel):
    repository: str
    tag: str | None = None


class AutoscalingBase(BaseModel):
    type: str
    enabled: bool | None = None
    min_replicas: int | None = None
    max_replicas: int | None = None


class AutoscalingHPA(AutoscalingBase):
    type: str = "HPA"
    target_cpu_utilization_percentage: int | None = None
    target_memory_utilization_percentage: int | None = None


class Env(BaseModel):
    name: str
    value: str


class Container(BaseModel):
    command: list[str] | None = None
    args: list[str] | None = None
    env: list[Env] = Field(default_factory=list)


class Service(BaseModel):
    enabled: bool
    port: int


class CustomDeploymentModel(BaseModel):
    preset: Preset = Field(description="Name of the preset configuration to use")
    http_auth: bool = Field(
        default=True, description="Enable/disable HTTP authentication"
    )
    name_override: str | None = Field(
        default=None, description="Override name for the deployment"
    )
    image: ContainerImage = Field(..., description="Container image configuration")
    autoscaling: AutoscalingHPA | None = Field(
        default=None, description="Autoscaling configuration. Currently not used"
    )
    container: Container | None = Field(
        default=None, description="Container configuration settings"
    )
    service: Service | None = Field(
        default=None, description="Service configuration settings"
    )
    ingress: Ingress | None = Field(
        default=None, description="Ingress configuration settings"
    )


class CustomDeploymentInputs(AppInputsV2):
    custom_deployment: CustomDeploymentModel


class CustomDeploymentOutputs(AppOutputsV2):
    internal_web_app_url: RestAPI
