from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


class AutoscalingBase(AbstractAppFieldType):
    type: str
    min_replicas: int = Field(
        default=1,
        json_schema_extra=SchemaExtraMetadata(
            title="Minimum Replicas",
            description="Set the minimum number of replicas for your deployment.",
        ).as_json_schema_extra(),
    )
    max_replicas: int = Field(
        default=5,
        json_schema_extra=SchemaExtraMetadata(
            title="Maximum Replicas",
            description="Limit the maximum number of replicas for your deployment.",
        ).as_json_schema_extra(),
    )


class AutoscalingHPA(AutoscalingBase):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Autoscaling HPA",
            description="Autoscaling configuration for Horizontal Pod Autoscaler.",
        ).as_json_schema_extra(),
    )
    target_cpu_utilization_percentage: int = Field(
        default=80,
        json_schema_extra=SchemaExtraMetadata(
            title="Target CPU Utilization Percentage",
            description="Choose target CPU utilization percentage for autoscaling.",
        ).as_json_schema_extra(),
    )
    target_memory_utilization_percentage: int | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Target Memory Utilization Percentage",
            description="Choose target memory utilization percentage for autoscaling.",
        ).as_json_schema_extra(),
    )
