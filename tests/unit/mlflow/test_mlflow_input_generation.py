import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import (
    ApoloFilesPath,
    IngressHttp,
    Preset,
)
from apolo_app_types.protocols.mlflow import (
    MLFlowAppInputs,
    MLFlowMetadataPostgres,
    MLFlowMetadataSQLite,
    PostgresURI,
)

from tests.unit.constants import APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_values_mlflow_generation_default_sqlite(
    setup_clients, mock_get_preset_cpu
):
    """
    Test that MLFlow defaults to sqlite:// and the default PVC name
    when no metadata_storage is provided.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress_http=IngressHttp(clusterName="test"),
        metadata_storage=MLFlowMetadataSQLite(),
        artifact_store=ApoloFilesPath(
            path="storage://test-cluster/myorg/proj/mlflow-artifacts"
        ),
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=input_data,
        apolo_client=setup_clients,
        app_type=AppType.MLFlow,
        app_name="my-mlflow",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    # Confirm environment var MLFLOW_TRACKING_URI = sqlite://...
    env_vars = helm_params["container"]["env"]
    tracking_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_TRACKING_URI"), None
    )
    assert tracking_env["value"] == "sqlite:///mlflow-data/mlflow.db"

    # Confirm we have a PVC volume mount
    assert "volumes" in helm_params
    assert len(helm_params["volumes"]) == 1
    assert helm_params["volumes"][0]["name"] == "mlflow-db-pvc"
    assert (
        helm_params["volumes"][0]["persistentVolumeClaim"]["claimName"]
        == "mlflow-sqlite-storage"
    )

    assert "volumeMounts" in helm_params
    assert len(helm_params["volumeMounts"]) == 1
    assert helm_params["volumeMounts"][0]["name"] == "mlflow-db-pvc"
    assert helm_params["volumeMounts"][0]["mountPath"] == "/mlflow-data"

    # Confirm artifact store configuration
    artifact_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_ARTIFACT_ROOT"), None
    )
    assert artifact_env is not None
    assert artifact_env["value"] == "file:///mlflow-artifacts"

    # Confirm service is 5000
    assert helm_params["service"]["ports"][0]["containerPort"] == 5000
    # Confirm "application=mlflow" label
    assert helm_params["labels"]["application"] == "mlflow"


@pytest.mark.asyncio
async def test_values_mlflow_generation_sqlite_explicit_no_pvc_name(
    setup_clients, mock_get_preset_cpu
):
    """
    Test that MLFlow uses the default PVC name when SQLite is chosen
    but no pvc_name is provided.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress_http=IngressHttp(clusterName="test"),
        metadata_storage=MLFlowMetadataSQLite(),
        artifact_store=ApoloFilesPath(path="storage://foo/bar/baz"),
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=input_data,
        apolo_client=setup_clients,
        app_type=AppType.MLFlow,
        app_name="my-mlflow",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    # Assert SQLite URI
    env_vars = helm_params["container"]["env"]
    tracking_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_TRACKING_URI"), None
    )
    assert tracking_env["value"] == "sqlite:///mlflow-data/mlflow.db"

    # Assert default PVC name
    assert (
        helm_params["volumes"][0]["persistentVolumeClaim"]["claimName"]
        == "mlflow-sqlite-storage"
    )


@pytest.mark.asyncio
async def test_values_mlflow_generation_sqlite_explicit_custom_pvc_name(
    setup_clients, mock_get_preset_cpu
):
    """
    Test that MLFlow uses the custom PVC name when SQLite is chosen
    and a pvc_name is provided.
    """
    custom_pvc_name = "my-custom-pvc"
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress_http=IngressHttp(clusterName="test"),
        metadata_storage=MLFlowMetadataSQLite(pvc_name=custom_pvc_name),
        artifact_store=ApoloFilesPath(path="storage://foo/bar/baz"),
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=input_data,
        apolo_client=setup_clients,
        app_type=AppType.MLFlow,
        app_name="my-mlflow",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    # Assert SQLite URI
    env_vars = helm_params["container"]["env"]
    tracking_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_TRACKING_URI"), None
    )
    assert tracking_env["value"] == "sqlite:///mlflow-data/mlflow.db"

    # Assert custom PVC name
    assert (
        helm_params["volumes"][0]["persistentVolumeClaim"]["claimName"]
        == custom_pvc_name
    )


@pytest.mark.asyncio
async def test_values_mlflow_generation_postgres_uri(
    setup_clients, mock_get_preset_cpu
):
    """
    Test that MLFlow config uses a user-supplied Postgres URI
    when provided.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress_http=IngressHttp(clusterName="test-cluster"),
        metadata_storage=MLFlowMetadataPostgres(
            postgres_uri=PostgresURI(
                uri="postgresql://user:pass@custom-host:5432/mlflow"
            ),
        ),
        artifact_store=ApoloFilesPath(
            path="storage://test-cluster/myorg/proj/mlflow-artifacts"
        ),
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=input_data,
        apolo_client=setup_clients,
        app_type=AppType.MLFlow,
        app_name="my-mlflow",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    # Check environment var for PG URI
    env_vars = helm_params["container"]["env"]
    tracking_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_TRACKING_URI"), None
    )
    assert tracking_env is not None
    assert tracking_env["value"] == "postgresql://user:pass@custom-host:5432/mlflow"

    # No PVC volumes
    assert "volumes" not in helm_params
    assert "volumeMounts" not in helm_params

    # Confirm artifact store configuration
    artifact_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_ARTIFACT_ROOT"), None
    )
    assert artifact_env is not None
    assert artifact_env["value"] == "file:///mlflow-artifacts"

    assert helm_params["labels"]["application"] == "mlflow"
