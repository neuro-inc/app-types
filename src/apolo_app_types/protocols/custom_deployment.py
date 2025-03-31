from pydantic import ConfigDict

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
    Service,
    StorageMounts,
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
    service: Service | None = None
    ingress: Ingress | None = None
    storage_mounts: StorageMounts | None = None


class CustomDeploymentOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
