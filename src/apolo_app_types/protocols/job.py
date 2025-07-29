from enum import StrEnum

from pydantic import BaseModel

from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.common.storage import StorageMounts


class JobPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class JobRestartPolicy(StrEnum):
    ALWAYS = "always"
    ON_FAILURE = "on-failure"
    NEVER = "never"


class ContainerTPUResource(BaseModel):
    type: str
    software_version: str


class ContainerResources(BaseModel):
    cpu: float
    memory: int | None = None
    memory_mb: int | None = None
    nvidia_gpu: int | None = None
    amd_gpu: int | None = None
    intel_gpu: int | None = None
    nvidia_gpu_model: str | None = None
    amd_gpu_model: str | None = None
    intel_gpu_model: str | None = None
    shm: bool | None = None
    tpu: ContainerTPUResource | None = None


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
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    preset_name: str | None = None
    priority: JobPriority = JobPriority.NORMAL
    scheduler_enabled: bool = False
    preemptible_node: bool = False
    restart_policy: JobRestartPolicy = JobRestartPolicy.NEVER
    max_run_time_minutes: int | None = None
    schedule_timeout: float | None = None
    energy_schedule_name: str | None = None
    pass_config: bool = False
    wait_for_jobs_quota: bool = False
    privileged: bool = False
    image: str
    resources: ContainerResources
    entrypoint: str | None = None
    command: str | None = None
    env: dict[str, str] | None = None
    secret_env: dict[str, ApoloSecret] | None = None
    storage_mounts: StorageMounts | None = None
    secret_volumes: list[SecretVolume] | None = None
    disk_volumes: list[DiskVolume] | None = None
    http: ContainerHTTPServer | None = None
    working_dir: str | None = None


class JobAppOutput(BaseModel):
    job_id: str | None = None
    job_status: str | None = None
    job_uri: str | None = None
