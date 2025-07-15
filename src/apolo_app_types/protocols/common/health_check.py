from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class ProbeType(str, Enum):
    HTTP = "HTTP"
    GRPC = "gRPC"
    TCP = "TCP"
    EXEC = "Exec"


class HealthCheckConfigBase(AbstractAppFieldType):
    """Base class for health check configurations."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Health Check Config Base",
            description="Base configuration for health checks.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    port: int = Field(
        default=8080,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Port",
            description="Port to make a connection for the Custom Deployment instance",
        ).as_json_schema_extra(),
    )


class HTTPHealthCheckConfig(HealthCheckConfigBase):
    """
    HTTP-specific health check configuration.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Health Check",
            description="Configuration for HTTP health checks.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    probe_type: Literal[ProbeType.HTTP] = Field(default=ProbeType.HTTP)
    path: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Path",
            description="Path to access on the HTTP server",
        ).as_json_schema_extra(),
    )
    http_headers: dict[str, str] | None = Field(
        None,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Headers",
            description="Custom headers to set in the request",
        ).as_json_schema_extra(),
    )


class GRPCHealthCheckConfig(HealthCheckConfigBase):
    """
    gRPC-specific health check configuration.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="gRPC Health Check",
            description="Configuration for gRPC health checks.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    probe_type: Literal[ProbeType.GRPC] = Field(default=ProbeType.GRPC)
    service: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Service",
            description="The name of the gRPC service to probe",
        ).as_json_schema_extra(),
    )


class TCPHealthCheckConfig(HealthCheckConfigBase):
    """
    TCP-specific health check configuration.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="TCP Health Check",
            description="Configuration for TCP health checks.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    probe_type: Literal[ProbeType.TCP] = Field(default=ProbeType.TCP)
    # No additional fields needed for TCP, just the connection attempt itself


class ExecHealthCheckConfig(AbstractAppFieldType):
    """
    Exec-specific health check configuration.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Exec Health Check",
            description="Configuration for exec health checks.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    probe_type: Literal[ProbeType.EXEC] = Field(default=ProbeType.EXEC)
    command: list[str] = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Command",
            description="Command to execute for the health check",
        ).as_json_schema_extra(),
    )


HealthCheckConfig = (
    HTTPHealthCheckConfig
    | GRPCHealthCheckConfig
    | TCPHealthCheckConfig
    | ExecHealthCheckConfig
)


class HealthCheck(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Health Check",
            description="Configuration for health checks on the application.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    initial_delay: int = Field(
        0,
        ge=0,
        le=240,
        json_schema_extra=SchemaExtraMetadata(
            title="Initial Delay",
            description="Number of seconds after the container has started "
            "before performing the first probe",
        ).as_json_schema_extra(),
    )
    period: int = Field(
        10,
        ge=1,
        le=240,
        json_schema_extra=SchemaExtraMetadata(
            title="Period",
            description="Number of seconds to wait between starting a probe attempt",
        ).as_json_schema_extra(),
    )
    failure_threshold: int = Field(
        3,
        json_schema_extra=SchemaExtraMetadata(
            title="Failure Threshold",
            description="Number of times to retry the probe before marking "
            "the container as Unready",
        ).as_json_schema_extra(),
    )
    timeout: int = Field(
        1,
        ge=1,
        le=240,
        json_schema_extra=SchemaExtraMetadata(
            title="Timeout",
            description="Number of seconds after which the probe times out",
        ).as_json_schema_extra(),
    )

    health_check_config: HealthCheckConfig

    @field_validator("timeout")
    @classmethod
    def timeout_less_than_period(cls, v: int, info) -> int:  # type: ignore
        if "period" in info.data and v > info.data["period"]:
            err = "Timeout value shouldn't exceed Period seconds"
            raise ValueError(err)
        return v


# Union type for accepting any of the health check types


class HealthCheckProbesConfig(AbstractAppFieldType):
    """
    Configuration for health check probes.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Health Check Probes",
            description="Configuration for health check probes.",
            meta_type=SchemaMetaType.INLINE,
        ).as_json_schema_extra(),
    )
    startup: HealthCheck | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Startup Probe",
            description="Configuration for startup probe",
        ).as_json_schema_extra(),
    )
    liveness: HealthCheck | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Liveness Probe",
            description="Configuration for liveness probe",
        ).as_json_schema_extra(),
    )
    readiness: HealthCheck | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Readiness Probe",
            description="Configuration for liveness probe",
        ).as_json_schema_extra(),
    )
