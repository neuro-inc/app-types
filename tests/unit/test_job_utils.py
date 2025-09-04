from decimal import Decimal
from unittest.mock import MagicMock, patch

import apolo_sdk
import pytest
from yarl import URL

from apolo_app_types.job_utils import JobRunParams, prepare_job_run_params
from apolo_app_types.protocols.common import ApoloSecret, Env, Preset
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
    StorageMounts,
)
from apolo_app_types.protocols.job import (
    JobAdvancedConfig,
    JobAppInput,
    JobImageConfig,
    JobMetadataConfig,
    JobPriority,
    JobResourcesConfig,
    JobRestartPolicy,
    JobSchedulingConfig,
    SecretVolume,
)


def test_prepare_job_run_params_minimal():
    """Test prepare_job_run_params with minimal configuration."""
    job_input = JobAppInput(
        image=JobImageConfig(image="python:3.9"),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=2.0,
            memory=8,
            credits_per_hour=Decimal("0.05"),
            available_resource_pool_names=("cpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    assert isinstance(result, JobRunParams)
    assert result.name == "test-app-test-ins"  # truncated to 8 chars
    assert result.tags == ["instance_id:test-instance-123"]
    assert result.description is None  # Empty string converted to None
    assert result.org_name == "test-org"
    assert result.project_name == "test-project"
    assert result.priority == apolo_sdk.JobPriority.NORMAL
    assert result.restart_policy == apolo_sdk.JobRestartPolicy.NEVER
    assert result.life_span is None  # 0 minutes means unlimited

    container = result.container
    assert container.image.name == "python:3.9"
    assert container.resources.cpu == 2.0
    assert container.resources.memory == 8
    assert container.resources.shm is True
    assert container.env == {}
    assert container.secret_env == {}
    assert container.volumes == []
    assert container.secret_files == []
    assert container.entrypoint is None  # Empty string converted to None
    assert container.command is None  # Empty string converted to None
    assert container.working_dir is None  # Empty string converted to None


def test_prepare_job_run_params_with_custom_name():
    """Test prepare_job_run_params with custom job name."""
    job_input = JobAppInput(
        image=JobImageConfig(image="python:3.9"),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
        metadata=JobMetadataConfig(name="my-custom-job"),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=2.0,
            memory=8,
            credits_per_hour=Decimal("0.05"),
            available_resource_pool_names=("cpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    assert result.name == "my-custom-job"


def test_prepare_job_run_params_with_env_vars():
    """Test prepare_job_run_params with environment variables."""
    job_input = JobAppInput(
        image=JobImageConfig(
            image="python:3.9",
            env=[
                Env(name="ENV_VAR1", value="value1"),
                Env(name="ENV_VAR2", value="value2"),
                Env(name="EMPTY_VAR", value=""),  # Should be excluded
            ],
            secret_env=[Env(name="SECRET_VAR", value=ApoloSecret(key="my-secret"))],
        ),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=2.0,
            memory=8,
            credits_per_hour=Decimal("0.05"),
            available_resource_pool_names=("cpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    container = result.container
    assert container.env == {"ENV_VAR1": "value1", "ENV_VAR2": "value2"}
    assert container.secret_env == {"SECRET_VAR": URL("secret://my-secret")}


def test_prepare_job_run_params_with_storage_mounts():
    """Test prepare_job_run_params with storage mounts."""
    job_input = JobAppInput(
        image=JobImageConfig(image="python:3.9"),
        resources=JobResourcesConfig(
            preset=Preset(name="cpu-small"),
            storage_mounts=StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path="storage://cluster/org/project/data"
                        ),
                        mount_path=MountPath(path="/data"),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path="storage://cluster/org/project/config"
                        ),
                        mount_path=MountPath(path="/config"),
                        mode=ApoloMountMode(mode="r"),
                    ),
                ]
            ),
        ),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=2.0,
            memory=8,
            credits_per_hour=Decimal("0.05"),
            available_resource_pool_names=("cpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    container = result.container
    assert len(container.volumes) == 2

    # Check first volume (read-write)
    vol1 = container.volumes[0]
    assert str(vol1.storage_uri) == "storage://cluster/org/project/data"
    assert vol1.container_path == "/data"
    assert vol1.read_only is False

    # Check second volume (read-only)
    vol2 = container.volumes[1]
    assert str(vol2.storage_uri) == "storage://cluster/org/project/config"
    assert vol2.container_path == "/config"
    assert vol2.read_only is True


def test_prepare_job_run_params_with_secret_volumes():
    """Test prepare_job_run_params with secret volumes."""
    job_input = JobAppInput(
        image=JobImageConfig(image="python:3.9"),
        resources=JobResourcesConfig(
            preset=Preset(name="cpu-small"),
            secret_volumes=[
                SecretVolume(
                    src_secret_uri=ApoloSecret(key="app-secret"),
                    dst_path="/secrets/app-secret",
                ),
                SecretVolume(
                    src_secret_uri=ApoloSecret(key="db-credentials"),
                    dst_path="/secrets/db-credentials",
                ),
            ],
        ),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=2.0,
            memory=8,
            credits_per_hour=Decimal("0.05"),
            available_resource_pool_names=("cpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    container = result.container
    assert len(container.secret_files) == 2

    # Check first secret file
    sf1 = container.secret_files[0]
    assert str(sf1.secret_uri) == "secret://app-secret"
    assert sf1.container_path == "/secrets/app-secret"

    # Check second secret file
    sf2 = container.secret_files[1]
    assert str(sf2.secret_uri) == "secret://db-credentials"
    assert sf2.container_path == "/secrets/db-credentials"


def test_prepare_job_run_params_with_all_options():
    """Test prepare_job_run_params with all configuration options."""
    job_input = JobAppInput(
        image=JobImageConfig(
            image="python:3.9",
            entrypoint="/bin/bash",
            command="-c 'python train.py'",
            working_dir="/app",
            env=[Env(name="PYTHONPATH", value="/app/src")],
            secret_env=[Env(name="API_KEY", value=ApoloSecret(key="api-credentials"))],
        ),
        resources=JobResourcesConfig(preset=Preset(name="gpu-large")),
        metadata=JobMetadataConfig(
            name="full-featured-job",
            description="A job with all features enabled",
            tags=["ml", "training"],
        ),
        scheduling=JobSchedulingConfig(
            priority=JobPriority.HIGH,
            scheduler_enabled=True,
            preemptible_node=True,
            restart_policy=JobRestartPolicy.ON_FAILURE,
            max_run_time_minutes=120,
            schedule_timeout=60.0,
            energy_schedule_name="green-schedule",
            wait_for_jobs_quota=True,
        ),
        advanced=JobAdvancedConfig(
            pass_config=True,
            privileged=True,
        ),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=4.0,
            memory=16,
            credits_per_hour=Decimal("0.2"),
            available_resource_pool_names=("gpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    assert result.name == "full-featured-job"
    assert result.description == "A job with all features enabled"
    assert result.tags == ["ml", "training", "instance_id:test-instance-123"]
    assert result.scheduler_enabled is True
    assert result.pass_config is True
    assert result.wait_for_jobs_quota is True
    assert result.schedule_timeout == 60.0
    assert result.restart_policy == apolo_sdk.JobRestartPolicy.ON_FAILURE
    assert result.life_span == 7200  # 120 minutes * 60 seconds
    assert result.priority == apolo_sdk.JobPriority.HIGH

    container = result.container
    assert container.entrypoint == "/bin/bash"
    assert container.command == "-c 'python train.py'"
    assert container.working_dir == "/app"
    assert container.env == {"PYTHONPATH": "/app/src"}
    assert container.secret_env == {"API_KEY": URL("secret://api-credentials")}
    assert container.resources.cpu == 4.0
    assert container.resources.memory == 16


def test_prepare_job_run_params_no_image_raises_error():
    """Test that prepare_job_run_params raises ValueError when no image is provided."""
    job_input = JobAppInput(
        image=JobImageConfig(image=""),  # Empty image should raise error
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
    )

    client = MagicMock()

    with pytest.raises(ValueError, match="Container image is required"):
        prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )


def test_prepare_job_run_params_unlimited_runtime():
    """Test that max_run_time_minutes=0 results in unlimited runtime."""
    job_input = JobAppInput(
        image=JobImageConfig(image="python:3.9"),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
        scheduling=JobSchedulingConfig(max_run_time_minutes=0),
    )

    client = MagicMock()

    with patch("apolo_app_types.helm.apps.common.get_preset") as mock_get_preset:
        mock_preset = apolo_sdk.Preset(
            cpu=2.0,
            memory=8,
            credits_per_hour=Decimal("0.05"),
            available_resource_pool_names=("cpu_pool",),
        )
        mock_get_preset.return_value = mock_preset

        result = prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )

    assert result.life_span is None
