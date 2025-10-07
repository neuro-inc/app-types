import pytest

from apolo_app_types.job_utils import prepare_job_run_params
from apolo_app_types.protocols.common import ApoloSecret, Env, Preset, RestAPI
from apolo_app_types.protocols.job import (
    JobAppInput,
    JobImageConfig,
    JobIntegrationsConfig,
    JobResourcesConfig,
    JobSchedulingConfig,
)
from apolo_app_types.protocols.mlflow import MLFlowTrackingServerURL


def test_prepare_job_with_mlflow_integration(setup_clients, mock_get_preset_cpu):
    job_input = JobAppInput(
        image=JobImageConfig(image="python:3.9"),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
        scheduling=JobSchedulingConfig(max_run_time_minutes=0),
        integrations=JobIntegrationsConfig(
            mlflow_integration=MLFlowTrackingServerURL(
                internal_url=RestAPI(host="mlflow.example.com")
            )
        ),
    )

    client = setup_clients

    result = prepare_job_run_params(
        job_input=job_input,
        app_instance_id="test-instance-123",
        app_instance_name="test-app",
        org_name="test-org",
        project_name="test-project",
        client=client,
    )

    assert result.env["MLFLOW_TRACKING_URI"] == "http://mlflow.example.com:80/"


def test_prepare_job_with_mlflow_integration_conflicts_with_env(
    setup_clients, mock_get_preset_cpu
):
    job_input = JobAppInput(
        image=JobImageConfig(
            image="python:3.9",
            env=[Env(name="MLFLOW_TRACKING_URI", value="http://other.example.com:80/")],
        ),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
        scheduling=JobSchedulingConfig(max_run_time_minutes=0),
        integrations=JobIntegrationsConfig(
            mlflow_integration=MLFlowTrackingServerURL(
                internal_url=RestAPI(host="mlflow.example.com")
            )
        ),
    )

    client = setup_clients

    with pytest.raises(
        ValueError,
        match="MLFLOW_TRACKING_URI env var conflicts with MLFlow integration.",
    ):
        prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )


def test_prepare_job_with_mlflow_integration_conflicts_with_secret_env(
    setup_clients, mock_get_preset_cpu
):
    job_input = JobAppInput(
        image=JobImageConfig(
            image="python:3.9",
            env=[Env(name="MLFLOW_TRACKING_URI", value=ApoloSecret(key="somethinbg"))],
        ),
        resources=JobResourcesConfig(preset=Preset(name="cpu-small")),
        scheduling=JobSchedulingConfig(max_run_time_minutes=0),
        integrations=JobIntegrationsConfig(
            mlflow_integration=MLFlowTrackingServerURL(
                internal_url=RestAPI(host="mlflow.example.com")
            )
        ),
    )

    client = setup_clients

    with pytest.raises(
        ValueError,
        match="MLFLOW_TRACKING_URI env var conflicts with MLFlow integration.",
    ):
        prepare_job_run_params(
            job_input=job_input,
            app_instance_id="test-instance-123",
            app_instance_name="test-app",
            org_name="test-org",
            project_name="test-project",
            client=client,
        )
