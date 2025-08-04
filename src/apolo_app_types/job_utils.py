from dataclasses import dataclass

import apolo_sdk
from yarl import URL

from apolo_app_types.protocols.job import JobAppInput


@dataclass
class JobRunParams:
    container: "apolo_sdk.Container"
    name: str
    tags: list[str]
    description: str | None
    scheduler_enabled: bool
    pass_config: bool
    wait_for_jobs_quota: bool
    schedule_timeout: float | None
    restart_policy: "apolo_sdk.JobRestartPolicy"
    life_span: float | None
    org_name: str
    priority: "apolo_sdk.JobPriority"
    project_name: str


def prepare_job_run_params(
    job_input: JobAppInput,
    app_instance_id: str,
    app_instance_name: str,
    org_name: str,
    project_name: str,
) -> JobRunParams:
    """Prepare all parameters for apolo_client.jobs.run() call."""
    if not job_input.image:
        msg = "Container image is required"
        raise ValueError(msg)

    resources = job_input.resources

    # Convert StorageMounts to apolo_sdk.Volume objects
    volumes = []
    if job_input.storage_mounts:
        for mount in job_input.storage_mounts.mounts:
            read_only = mount.mode.mode.value == "r"
            volume = apolo_sdk.Volume(
                storage_uri=URL(mount.storage_uri.path),
                container_path=mount.mount_path.path,
                read_only=read_only,
            )
            volumes.append(volume)

    # Convert SecretVolume to apolo_sdk.SecretFile objects
    secret_files = []
    if job_input.secret_volumes:
        for secret_volume in job_input.secret_volumes:
            secret_file = apolo_sdk.SecretFile(
                secret_uri=URL(f"secret://{secret_volume.src_secret_uri.key}"),
                container_path=secret_volume.dst_path,
            )
            secret_files.append(secret_file)

    container = apolo_sdk.Container(
        image=apolo_sdk.RemoteImage.new_external_image(name=job_input.image),
        resources=apolo_sdk.Resources(
            cpu=resources.cpu,
            memory=resources.memory_mb * 1024 * 1024
            if resources.memory_mb
            else 128 * 1024 * 1024,
            nvidia_gpu=resources.nvidia_gpu,
            nvidia_gpu_model=resources.nvidia_gpu_model,
            shm=resources.shm if resources.shm is not None else True,
        ),
        entrypoint=job_input.entrypoint,
        command=job_input.command,
        working_dir=job_input.working_dir,
        env=job_input.env or {},
        secret_env={
            k: URL(f"secret://{v.key}") for k, v in (job_input.secret_env or {}).items()
        },
        volumes=volumes,
        secret_files=secret_files,
        tty=True,
    )

    job_name = job_input.name or f"{app_instance_name}-{app_instance_id[:8]}"

    tags = (job_input.tags or []) + [f"instance_id:{app_instance_id}"]

    return JobRunParams(
        container=container,
        name=job_name,
        tags=tags,
        description=job_input.description,
        scheduler_enabled=job_input.scheduler_enabled,
        pass_config=job_input.pass_config,
        wait_for_jobs_quota=job_input.wait_for_jobs_quota,
        schedule_timeout=job_input.schedule_timeout,
        restart_policy=apolo_sdk.JobRestartPolicy(job_input.restart_policy),
        life_span=job_input.max_run_time_minutes * 60
        if job_input.max_run_time_minutes
        else None,
        org_name=org_name,
        priority=apolo_sdk.JobPriority[job_input.priority.value.upper()],
        project_name=project_name,
    )
