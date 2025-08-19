from enum import StrEnum

from pydantic import BaseModel, Field

from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.preset import Preset
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


class ContainerTPUResource(BaseModel):
    type: str = Field(description="TPU type specification")
    software_version: str = Field(description="TPU software version")


class ContainerResources(BaseModel):
    cpu: float = Field(description="Number of CPU cores")
    memory: int = Field(default=0, description="Memory in bytes")
    memory_mb: int = Field(default=0, description="Memory in megabytes")
    nvidia_gpu: int = Field(default=0, description="Number of NVIDIA GPUs")
    amd_gpu: int = Field(default=0, description="Number of AMD GPUs")
    intel_gpu: int = Field(default=0, description="Number of Intel GPUs")
    nvidia_gpu_model: str = Field(
        default="", description="NVIDIA GPU model specification"
    )
    amd_gpu_model: str = Field(default="", description="AMD GPU model specification")
    intel_gpu_model: str = Field(
        default="", description="Intel GPU model specification"
    )
    shm: bool = Field(default=False, description="Enable shared memory")
    tpu: ContainerTPUResource | None = Field(
        default=None, description="TPU resource configuration"
    )


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
    image: str = Field(description="Container image to run")
    entrypoint: str = Field(default="", description="Container entrypoint")
    command: str = Field(default="", description="Container command")
    env: list[Env] = Field(default_factory=list, description="Environment variables")
    secret_env: list[Env] = Field(
        default_factory=list, description="Secret environment variables"
    )
    working_dir: str = Field(
        default="", description="Working directory inside container"
    )
    name: str = Field(default="", description="Job name")
    description: str = Field(default="", description="Job description")
    tags: list[str] = Field(default_factory=list, description="Job tags")
    preset: Preset = Field(description="Resource preset configuration")
    priority: JobPriority = Field(
        default=JobPriority.NORMAL, description="Job priority level"
    )
    scheduler_enabled: bool = Field(default=False, description="Enable job scheduler")
    preemptible_node: bool = Field(default=False, description="Use preemptible nodes")
    restart_policy: JobRestartPolicy = Field(
        default=JobRestartPolicy.NEVER, description="Job restart policy"
    )
    max_run_time_minutes: int = Field(
        default=0, description="Maximum runtime in minutes (0 for unlimited)"
    )
    schedule_timeout: float = Field(
        default=0.0, description="Schedule timeout in seconds"
    )
    energy_schedule_name: str = Field(default="", description="Energy schedule name")
    pass_config: bool = Field(default=False, description="Pass configuration to job")
    wait_for_jobs_quota: bool = Field(default=False, description="Wait for jobs quota")
    privileged: bool = Field(
        default=False, description="Run container in privileged mode"
    )
    resources: ContainerResources = Field(description="Container resource requirements")
    storage_mounts: StorageMounts | None = Field(
        default=None, description="Storage mount configuration"
    )
    secret_volumes: list[SecretVolume] | None = Field(
        default=None, description="Secret volume mounts"
    )
    disk_volumes: list[DiskVolume] | None = Field(
        default=None, description="Disk volume mounts"
    )
    http: ContainerHTTPServer | None = Field(
        default=None, description="HTTP server configuration"
    )


class JobAppOutput(BaseModel):
    job_id: str | None = None
    job_status: str | None = None
    job_uri: str | None = None
