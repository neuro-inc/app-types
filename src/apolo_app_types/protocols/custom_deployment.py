from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AppOutputs,
    AutoscalingHPA,
    Container,
    ContainerImage,
    IngressHttp,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
    StorageMounts,
)
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.health_check import (
    HealthCheckProbesConfig,
)
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.common.storage import MountPath


class NetworkingConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Network Configuration",
            description="Configure custom networking "
            "options for your deployment, including ports and ingress settings.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    service_enabled: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            title="Service Enabled",
            description="Enable or disable the internal "
            "network service for the deployment.",
        ).as_json_schema_extra(),
    )

    ingress_http: IngressHttp | None = Field(
        default_factory=lambda: IngressHttp(),
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Ingress",
            description="Define HTTP ingress configuration"
            " for exposing services over the web.",
        ).as_json_schema_extra(),
    )

    ports: list[Port] = Field(
        default_factory=lambda: [Port()],
        json_schema_extra=SchemaExtraMetadata(
            title="Exposed Ports",
            description="Specify which ports should be exposed by the application.",
        ).as_json_schema_extra(),
    )


class ConfigMapKeyValue(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Key-Value Pair",
            description="Define a key-value pair."
            " Each key will be a file in the mounted directory.",
        ).as_json_schema_extra(),
    )
    key: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Key",
            description="The key for the entry. "
            "It will be used as a file name in the mounted directory.",
        ).as_json_schema_extra(),
    )
    value: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Value",
            description="The value associated with the key.",
        ).as_json_schema_extra(),
    )


class ConfigMap(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Mount Configuration Data",
            description="Store non-sensitive"
            " configuration data in key-value format"
            " that can be mounted into the"
            " application as files.",
        ).as_json_schema_extra(),
    )
    mount_path: MountPath = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Mount Path",
            description="The path where the key-value pairs"
            " will be mounted in the container.",
        ).as_json_schema_extra(),
    )
    data: list[ConfigMapKeyValue]


class CustomDeploymentInputs(AppInputs):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Custom Deployment",
            description="Configuration for Custom Deployment.",
        ).as_json_schema_extra(),
    )
    preset: Preset
    image: ContainerImage
    autoscaling: AutoscalingHPA | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Autoscaling",
            description="Enable Autoscaling and configure it.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )
    container: Container | None = Field(
        None,
        json_schema_extra=SchemaExtraMetadata(
            title="Container",
            description="Enable Container configuration.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )
    config_map: ConfigMap | None = Field(default=None)
    storage_mounts: StorageMounts | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Mounts",
            description="Enable Storage mounts configuration.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )
    networking: NetworkingConfig = Field(default_factory=lambda: NetworkingConfig())
    health_checks: HealthCheckProbesConfig | None = Field(default=None)


class CustomDeploymentOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Web App inter-cluster URL",
            description=(
                "Use this endpoint to reach out to your app via internal network "
                "within the cluster. Platform authorization is not applied here "
                "but only the workloads from the same project can access it."
            ),
        ).as_json_schema_extra(),
    )
    external_web_app_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External Web App URL",
            description=(
                "Use this endpoint to reach out to your app via public network "
                "from outside the cluster. Platform authorization is applied "
                "here if you enabled it during the deployment."
            ),
        ).as_json_schema_extra(),
    )
