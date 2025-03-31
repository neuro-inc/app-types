from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from pydantic import ConfigDict


class AutoscalingBase(AbstractAppFieldType):
    type: str
    enabled: bool | None = None
    min_replicas: int | None = None
    max_replicas: int | None = None


class AutoscalingHPA(AutoscalingBase):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Autoscaling HPA",
            description="Autoscaling configuration for Horizontal Pod Autoscaler.",
        ).as_json_schema_extra(),
    )
    type: str = "HPA"
    target_cpu_utilization_percentage: int | None = None
    target_memory_utilization_percentage: int | None = None
