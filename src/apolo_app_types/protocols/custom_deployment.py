from pydantic import ConfigDict, Field

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppOutputs,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.containers import ContainerImage
from apolo_app_types.protocols.common.ingress import Ingress
from apolo_app_types.protocols.common.storage import ApoloFilesMount


class AutoscalingBase(AbstractAppFieldType):
    type: str
    enabled: bool | None = None
    min_replicas: int | None = None
    max_replicas: int | None = None


class AutoscalingHPA(AutoscalingBase):
    type: str = "HPA"
    target_cpu_utilization_percentage: int | None = None
    target_memory_utilization_percentage: int | None = None


class Env(AbstractAppFieldType):
    name: str
    value: str


class Container(AbstractAppFieldType):
    command: list[str] | None = None
    args: list[str] | None = None
    env: list[Env] = Field(default_factory=list)


class Service(AbstractAppFieldType):
    enabled: bool
    port: int


class DeploymentName(AbstractAppFieldType):
    name: str | None = Field(
        default=None,
        title="Deployment Name",
        description="Override name for the deployment",
    )


class StorageMounts(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Mounts",
            description="Mount external storage paths",
        ).as_json_schema_extra(),
    )
    mounts: list[ApoloFilesMount] = Field(
        default_factory=list,
        description="List of ApoloStorageMount objects to mount external storage paths",
    )


class CustomDeploymentInputs(AppInputs):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Custom Deployment",
            description="Configuration for Custom Deployment.",
        ).as_json_schema_extra(),
    )
    preset: Preset = Field(description="Name of the preset configuration to use")
    name_override: DeploymentName | None = Field(
        default=None,
        title="Deployment Name",
        description="Override name for the deployment",
    )
    image: ContainerImage = Field(
        ..., title="Container Image", description="Container image configuration"
    )
    autoscaling: AutoscalingHPA | None = Field(
        default=None,
        title="AutoScaling Settings",
        description="Autoscaling configuration. Currently not used",
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
    storage_mounts: StorageMounts | None = Field(
        default=None, description="Mount external storage paths"
    )


class CustomDeploymentOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
