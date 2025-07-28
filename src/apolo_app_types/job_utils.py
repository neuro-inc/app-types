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
    container_image = job_input.image
    if job_input.container:
        container_image = job_input.container.image

    if not container_image:
        msg = "Container image is required"
        raise ValueError(msg)

    resources = job_input.resources
    if job_input.container:
        resources = job_input.container.resources

    container = apolo_sdk.Container(
        image=apolo_sdk.RemoteImage.new_external_image(name=container_image),
        resources=apolo_sdk.Resources(
            cpu=resources.cpu if resources else 0.1,
            memory=resources.memory_mb * 1024 * 1024
            if resources and resources.memory_mb
            else 128 * 1024 * 1024,
            nvidia_gpu=resources.nvidia_gpu
            if resources and resources.nvidia_gpu
            else None,
            nvidia_gpu_model=resources.nvidia_gpu_model
            if resources and resources.nvidia_gpu_model
            else None,
            shm=resources.shm if resources and resources.shm is not None else True,
        ),
        entrypoint=job_input.entrypoint
        or (job_input.container.entrypoint if job_input.container else None),
        command=job_input.command
        or (job_input.container.command if job_input.container else None),
        working_dir=job_input.working_dir
        or (job_input.container.working_dir if job_input.container else None),
        env=job_input.env
        or (job_input.container.env if job_input.container else None)
        or {},
        secret_env={
            k: URL(v)
            for k, v in (
                job_input.secret_env
                or (job_input.container.secret_env if job_input.container else None)
                or {}
            ).items()
        },
        tty=job_input.tty
        or (job_input.container.tty if job_input.container else False),
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
