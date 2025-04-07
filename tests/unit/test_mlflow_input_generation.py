import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import (
    ApoloFilesPath,
    Ingress,
    Preset,
)
from apolo_app_types.protocols.mlflow import (
    ArtifactStoreConfig,
    HttpAuthConfig,
    MLFlowAppInputs,
    MLFlowSpecificInputs,
    MLFlowStorageBackendConfig,
    MLFlowStorageBackendEnum,
    PostgresURIConfig,
    SQLitePVCConfig,
)

from tests.unit.constants import APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_values_mlflow_generation_sqlite_pvc(setup_clients, mock_get_preset_cpu):
    """
    Test that MLFlow is configured with sqlite:// and a PVC mount
    when user chooses 'SQLITE' with a PVC name.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress=Ingress(enabled=True, clusterName="test"),
        mlflow_specific=MLFlowSpecificInputs(
            http_auth=HttpAuthConfig(enabled=True),
            storage_backend=MLFlowStorageBackendConfig(
                database=MLFlowStorageBackendEnum.SQLITE
            ),
            sqlite_pvc=SQLitePVCConfig(pvc_name="my-mlflow-db"),
            artifact_store=ArtifactStoreConfig(
                path=ApoloFilesPath(
                    path="storage://test-cluster/myorg/proj/mlflow-artifacts"
                )
            ),
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
    assert tracking_env is not None
    assert "sqlite:///" in tracking_env["value"]

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
    assert helm_params["service"]["port"] == 5000
    # Confirm "application=mlflow" label
    assert helm_params["labels"]["application"] == "mlflow"


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
        ingress=Ingress(enabled=False, clusterName="test-cluster"),
        mlflow_specific=MLFlowSpecificInputs(
            http_auth=HttpAuthConfig(enabled=False),
            storage_backend=MLFlowStorageBackendConfig(
                database=MLFlowStorageBackendEnum.POSTGRES
            ),
            postgres_uri=PostgresURIConfig(
                uri="postgresql://user:pass@custom-host:5432/mlflow"
            ),
            artifact_store=ArtifactStoreConfig(
                path=ApoloFilesPath(
                    path="storage://test-cluster/myorg/proj/mlflow-artifacts"
                )
            ),
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


@pytest.mark.asyncio
async def test_values_mlflow_generation_sqlite_no_pvc(
    setup_clients, mock_get_preset_cpu
):
    """
    Test that MLFlow raises an error when SQLite is chosen but no PVC name is provided.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress=Ingress(enabled=True, clusterName="test"),
        mlflow_specific=MLFlowSpecificInputs(
            http_auth=HttpAuthConfig(enabled=True),
            storage_backend=MLFlowStorageBackendConfig(
                database=MLFlowStorageBackendEnum.SQLITE
            ),
        ),
    )

    with pytest.raises(ValueError, match="SQLite chosen but no 'sqlite_pvc' provided."):
        await app_type_to_vals(
            input_=input_data,
            apolo_client=setup_clients,
            app_type=AppType.MLFlow,
            app_name="my-mlflow",
            namespace=DEFAULT_NAMESPACE,
            app_secrets_name=APP_SECRETS_NAME,
        )


@pytest.mark.asyncio
async def test_values_mlflow_generation_postgres_no_config(
    setup_clients, mock_get_preset_cpu
):
    """
    Test that MLFlow raises an error when Postgres is chosen
    but no URI is provided.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress=Ingress(enabled=True, clusterName="test"),
        mlflow_specific=MLFlowSpecificInputs(
            http_auth=HttpAuthConfig(enabled=True),
            storage_backend=MLFlowStorageBackendConfig(
                database=MLFlowStorageBackendEnum.POSTGRES
            ),
        ),
    )

    err_msg = "Postgres chosen but 'postgres_uri' not provided"
    with pytest.raises(ValueError, match=err_msg):
        await app_type_to_vals(
            input_=input_data,
            apolo_client=setup_clients,
            app_type=AppType.MLFlow,
            app_name="my-mlflow",
            namespace=DEFAULT_NAMESPACE,
            app_secrets_name=APP_SECRETS_NAME,
        )
