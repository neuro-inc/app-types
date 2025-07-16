from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


class AutoscalingBase(AbstractAppFieldType):
    min_replicas: int = Field(
        default=1,
        ge=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Minimum Replicas",
            description="Set the minimum number of replicas for your deployment.",
        ).as_json_schema_extra(),
    )
    max_replicas: int = Field(
        default=5,
        gt=0,
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
        gt=0,
        le=100,
        json_schema_extra=SchemaExtraMetadata(
            title="Target CPU Utilization Percentage",
            description="Choose target CPU utilization percentage for autoscaling.",
        ).as_json_schema_extra(),
    )
    target_memory_utilization_percentage: int | None = Field(
        default=None,
        gt=0,
        le=100,
        json_schema_extra=SchemaExtraMetadata(
            title="Target Memory Utilization Percentage",
            description="Choose target memory utilization percentage for autoscaling.",
        ).as_json_schema_extra(),
    )


class RequestRateConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Request Rate Configuration",
            description="Configuration for request rate based autoscaling.",
        ).as_json_schema_extra(),
    )
    granularity: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Granularity",
            description="Time in seconds to calculate request rate.",
        ).as_json_schema_extra(),
    )
    target_value: int = Field(
        default=100,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Target Value",
            description="Target request rate per second for autoscaling.",
        ).as_json_schema_extra(),
    )
    window_size: int = Field(
        default=60,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Window Size",
            description="Time in seconds to consider for request rate calculation.",
        ).as_json_schema_extra(),
    )


class AutoscalingKedaHTTP(AutoscalingBase):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Autoscaling HPA",
            description="Autoscaling configuration for Horizontal Pod Autoscaler.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )
    scaledown_period: int = Field(
        300,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Scaledown Period",
            description="Time in seconds to wait before scaling down.",
        ).as_json_schema_extra(),
    )
    request_rate: RequestRateConfig = Field(
        default=RequestRateConfig(),
        json_schema_extra=SchemaExtraMetadata(
            title="Request Rate Configuration",
            description="Configuration for request rate based autoscaling.",
        ).as_json_schema_extra(),
    )
