from dataclasses import dataclass

import apolo_sdk
from yarl import URL

from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.job import JobAppInput


@dataclass
class JobRunParams:
    image: "apolo_sdk.RemoteImage"
    preset_name: str
    entrypoint: str | None
    command: str | None
    working_dir: str | None
    http: "apolo_sdk.HTTPPort | None"
    env: dict[str, str]
    volumes: list["apolo_sdk.Volume"]
    secret_env: dict[str, URL]
    secret_files: list["apolo_sdk.SecretFile"]
    disk_volumes: list["apolo_sdk.DiskVolume"]
    tty: bool
    shm: bool
    name: str
    tags: list[str]
    description: str | None
    pass_config: bool
    wait_for_jobs_quota: bool
    schedule_timeout: float | None
    restart_policy: "apolo_sdk.JobRestartPolicy"
    life_span: float | None
    org_name: str
    priority: "apolo_sdk.JobPriority"
    project_name: str


def prepare_job_run_params(  # noqa: C901
    job_input: JobAppInput,
    app_instance_id: str,
    app_instance_name: str,
    org_name: str,
    project_name: str,
    client: apolo_sdk.Client,
) -> JobRunParams:
    """Prepare all parameters for apolo_client.jobs.start() call."""
    if not job_input.image.image or job_input.image.image.strip() == "":
        msg = "Container image is required"
        raise ValueError(msg)

    # Convert StorageMounts to apolo_sdk.Volume objects
    volumes = []
    if job_input.resources.storage_mounts:
        for mount in job_input.resources.storage_mounts.mounts:
            read_only = mount.mode.mode.value == "r"
            volume = apolo_sdk.Volume(
                storage_uri=URL(mount.storage_uri.path),
                container_path=mount.mount_path.path,
                read_only=read_only,
            )
            volumes.append(volume)

    # Convert SecretVolume to apolo_sdk.SecretFile objects
    secret_files = []
    if job_input.resources.secret_volumes:
        for secret_volume in job_input.resources.secret_volumes:
            secret_file = apolo_sdk.SecretFile(
                secret_uri=URL(
                    f"secret://{client.cluster_name}/{org_name}/{project_name}/{secret_volume.src_secret_uri.key}"
                ),
                container_path=secret_volume.dst_path,
            )
            secret_files.append(secret_file)

    env_dict = {}
    secret_env_dict = {}
    for env_var in job_input.image.env:
        if isinstance(env_var.value, ApoloSecret):
            secret_env_dict[env_var.name] = URL(
                f"secret://{client.cluster_name}/{org_name}/{project_name}/{env_var.value.key}"
            )
        elif isinstance(env_var.value, str):
            env_dict[env_var.name] = env_var.value

    # Process job integrations envs
    mlflow_integration = job_input.integrations.mlflow_integration
    if mlflow_integration.internal_url:
        if (
            "MLFLOW_TRACKING_URI" in env_dict
            or "MLFLOW_TRACKING_URI" in secret_env_dict
        ):
            err_msg = "MLFLOW_TRACKING_URI env var conflicts with MLFlow integration."
            raise ValueError(err_msg)
        env_dict["MLFLOW_TRACKING_URI"] = mlflow_integration.internal_url.complete_url

    job_name = (
        job_input.metadata.name.strip()
        if job_input.metadata.name.strip()
        else app_instance_name
    )

    tags = job_input.metadata.tags + [f"instance_id:{app_instance_id}"]

    return JobRunParams(
        image=apolo_sdk.RemoteImage.new_external_image(name=job_input.image.image),
        preset_name=job_input.resources.preset.name,
        entrypoint=job_input.image.entrypoint
        if job_input.image.entrypoint.strip()
        else None,
        command=job_input.image.command if job_input.image.command.strip() else None,
        working_dir=job_input.image.working_dir
        if job_input.image.working_dir.strip()
        else None,
        http=None,
        env=env_dict,
        volumes=volumes,
        secret_env=secret_env_dict,
        secret_files=secret_files,
        disk_volumes=[],
        tty=True,
        shm=True,
        name=job_name,
        tags=tags,
        description=job_input.metadata.description
        if job_input.metadata.description.strip()
        else None,
        pass_config=job_input.advanced.pass_config,
        wait_for_jobs_quota=job_input.scheduling.wait_for_jobs_quota,
        schedule_timeout=job_input.scheduling.schedule_timeout,
        restart_policy=apolo_sdk.JobRestartPolicy(job_input.scheduling.restart_policy),
        life_span=job_input.scheduling.max_run_time_minutes * 60
        if job_input.scheduling.max_run_time_minutes > 0
        else None,
        org_name=org_name,
        priority=apolo_sdk.JobPriority[job_input.scheduling.priority.value.upper()],
        project_name=project_name,
    )
