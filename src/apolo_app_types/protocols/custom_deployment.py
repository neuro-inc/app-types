from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AppOutputs,
    AutoscalingHPA,
    Container,
    ContainerImage,
    DeploymentName,
    Ingress,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
    StorageMounts,
)
from apolo_app_types.protocols.common.k8s import Port


class NetworkingConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Network Configuration",
            description="Configuration for Custom Deployment Networking.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )
    service_enabled: bool = Field(
        default=True,
        title="Service Enabled",
        description="Whether to enable the service.",
    )

    ingress: Ingress = Field(default_factory=lambda: Ingress(enabled=True))

    ports: list[Port] = Field(
        default_factory=lambda: [Port()],
        title="Ports",
        description="List of ports to expose.",
    )


class CustomDeploymentInputs(AppInputs):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Custom Deployment",
            description="Configuration for Custom Deployment.",
        ).as_json_schema_extra(),
    )
    preset: Preset
    name_override: DeploymentName | None = None
    image: ContainerImage
    autoscaling: AutoscalingHPA | None = None
    container: Container | None = None
    storage_mounts: StorageMounts | None = None
    networking: NetworkingConfig = Field(default_factory=lambda: NetworkingConfig())


class CustomDeploymentOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
