from dataclasses import dataclass

import apolo_sdk
from yarl import URL

from apolo_app_types.helm.apps.common import get_preset
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
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


def prepare_job_run_params(  # noqa: C901
    job_input: JobAppInput,
    app_instance_id: str,
    app_instance_name: str,
    org_name: str,
    project_name: str,
    client: apolo_sdk.Client,
) -> JobRunParams:
    """Prepare all parameters for apolo_client.jobs.run() call."""
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
                secret_uri=URL(f"secret://{secret_volume.src_secret_uri.key}"),
                container_path=secret_volume.dst_path,
            )
            secret_files.append(secret_file)

    # Convert env list to dict
    env_dict = {}
    for env_var in job_input.image.env:
        if isinstance(env_var.value, str) and env_var.value:
            env_dict[env_var.name] = env_var.value

    # Convert secret_env list to dict
    secret_env_dict = {}
    for env_var in job_input.image.secret_env:
        if isinstance(env_var.value, ApoloSecret):
            secret_env_dict[env_var.name] = URL(f"secret://{env_var.value.key}")

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

    preset = get_preset(client, job_input.resources.preset.name)

    container = apolo_sdk.Container(
        image=apolo_sdk.RemoteImage.new_external_image(name=job_input.image.image),
        resources=apolo_sdk.Resources(
            cpu=preset.cpu,
            memory=preset.memory,
            nvidia_gpu=preset.nvidia_gpu.count if preset.nvidia_gpu else None,
            amd_gpu=preset.amd_gpu.count if preset.amd_gpu else None,
            intel_gpu=preset.intel_gpu.count if preset.intel_gpu else None,
            nvidia_gpu_model=preset.nvidia_gpu.model if preset.nvidia_gpu else None,
            amd_gpu_model=preset.amd_gpu.model if preset.amd_gpu else None,
            intel_gpu_model=preset.intel_gpu.model if preset.intel_gpu else None,
            tpu_type=preset.tpu.type if preset.tpu else None,
            tpu_software_version=preset.tpu.software_version if preset.tpu else None,
            shm=True,  # Default to True as before
        ),
        entrypoint=job_input.image.entrypoint
        if job_input.image.entrypoint.strip()
        else None,
        command=job_input.image.command if job_input.image.command.strip() else None,
        working_dir=job_input.image.working_dir
        if job_input.image.working_dir.strip()
        else None,
        env=env_dict,
        secret_env=secret_env_dict,
        volumes=volumes,
        secret_files=secret_files,
        tty=True,
    )

    job_name = (
        job_input.metadata.name.strip()
        if job_input.metadata.name.strip()
        else app_instance_name
    )

    tags = job_input.metadata.tags + [f"instance_id:{app_instance_id}"]

    return JobRunParams(
        container=container,
        name=job_name,
        tags=tags,
        description=job_input.metadata.description
        if job_input.metadata.description.strip()
        else None,
        scheduler_enabled=job_input.scheduling.scheduler_enabled,
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
