from enum import StrEnum

from pydantic import BaseModel, Field

from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.common.storage import StorageMounts


class JobPriority(StrEnum):
    """Job priority levels for resource allocation."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class JobRestartPolicy(StrEnum):
    """Job restart policy for handling failures."""

    ALWAYS = "always"
    ON_FAILURE = "on-failure"
    NEVER = "never"


class SecretVolume(BaseModel):
    src_secret_uri: ApoloSecret
    dst_path: str


class DiskVolume(BaseModel):
    src_disk_uri: str
    dst_path: str
    read_only: bool = False


class ContainerHTTPServer(BaseModel):
    port: int
    health_check_path: str | None = None
    requires_auth: bool = False


class JobAppInput(BaseModel):
    image: str = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image",
            description="Container image to run",
        ).as_json_schema_extra(),
    )
    entrypoint: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Entrypoint",
            description="Container entrypoint",
        ).as_json_schema_extra(),
    )
    command: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Command",
            description="Container command",
        ).as_json_schema_extra(),
    )
    env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Environment Variables",
            description="Environment variables",
        ).as_json_schema_extra(),
    )
    secret_env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Secret Environment Variables",
            description="Secret environment variables",
        ).as_json_schema_extra(),
    )
    working_dir: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Working Directory",
            description="Working directory inside container",
        ).as_json_schema_extra(),
    )
    name: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Job Name",
            description="Job name",
        ).as_json_schema_extra(),
    )
    description: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Job Description",
            description="Job description",
        ).as_json_schema_extra(),
    )
    tags: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Job Tags",
            description="Job tags",
        ).as_json_schema_extra(),
    )
    preset: Preset = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Resource Preset",
            description="Resource preset configuration",
        ).as_json_schema_extra(),
    )
    priority: JobPriority = Field(
        default=JobPriority.NORMAL,
        json_schema_extra=SchemaExtraMetadata(
            title="Job Priority",
            description="Job priority level",
        ).as_json_schema_extra(),
    )
    scheduler_enabled: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Scheduler Enabled",
            description="Enable job scheduler",
        ).as_json_schema_extra(),
    )
    preemptible_node: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Preemptible Node",
            description="Use preemptible nodes",
        ).as_json_schema_extra(),
    )
    restart_policy: JobRestartPolicy = Field(
        default=JobRestartPolicy.NEVER,
        json_schema_extra=SchemaExtraMetadata(
            title="Restart Policy",
            description="Job restart policy",
        ).as_json_schema_extra(),
    )
    max_run_time_minutes: int = Field(
        default=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Max Runtime (Minutes)",
            description="Maximum runtime in minutes (0 for unlimited)",
        ).as_json_schema_extra(),
    )
    schedule_timeout: float = Field(
        default=0.0,
        json_schema_extra=SchemaExtraMetadata(
            title="Schedule Timeout",
            description="Schedule timeout in seconds",
        ).as_json_schema_extra(),
    )
    energy_schedule_name: str = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Energy Schedule Name",
            description="Energy schedule name",
        ).as_json_schema_extra(),
    )
    pass_config: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Pass Config",
            description="Pass configuration to job",
        ).as_json_schema_extra(),
    )
    wait_for_jobs_quota: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Wait for Jobs Quota",
            description="Wait for jobs quota",
        ).as_json_schema_extra(),
    )
    privileged: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Privileged Mode",
            description="Run container in privileged mode",
        ).as_json_schema_extra(),
    )
    storage_mounts: StorageMounts | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Mounts",
            description="Storage mount configuration",
        ).as_json_schema_extra(),
    )
    secret_volumes: list[SecretVolume] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Secret Volumes",
            description="Secret volume mounts",
        ).as_json_schema_extra(),
    )
    disk_volumes: list[DiskVolume] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Disk Volumes",
            description="Disk volume mounts",
        ).as_json_schema_extra(),
    )
    http: ContainerHTTPServer | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Server",
            description="HTTP server configuration",
        ).as_json_schema_extra(),
    )


class JobAppOutput(BaseModel):
    job_id: str | None = None
    job_status: str | None = None
    job_uri: str | None = None
