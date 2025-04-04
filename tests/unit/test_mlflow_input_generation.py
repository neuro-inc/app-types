import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.mlflow import (
    HttpAuthConfig,
    MLFlowAppInputs,
    MLFlowSpecificInputs,
    MLFlowStorageBackendConfig,
    MLFlowStorageBackendEnum,
    PostgresAppNameConfig,
)

from tests.unit.constants import APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_values_mlflow_generation_sqlite(setup_clients, mock_get_preset_cpu):
    """
    Test that MLFlow is configured with sqlite:// and a disk mount
    when user chooses 'SQLITE'.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress=Ingress(enabled=True, clusterName="test"),
        mlflow_specific=MLFlowSpecificInputs(
            http_auth=HttpAuthConfig(enabled=True),
            storage_backend=MLFlowStorageBackendConfig(
                backend=MLFlowStorageBackendEnum.SQLITE
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

    # Confirm we have a storage mount annotation for /mlflow-data
    assert "podAnnotations" in helm_params
    storage_annot = helm_params["podAnnotations"].get(
        "platform.apolo.us/inject-storage"
    )
    assert "/mlflow-data" in storage_annot

    # Confirm service is 5000
    assert helm_params["service"]["port"] == 5000
    # Confirm "application=mlflow" label
    assert helm_params["labels"]["application"] == "mlflow"


@pytest.mark.asyncio
async def test_values_mlflow_generation_postgres(setup_clients, mock_get_preset_cpu):
    """
    Test that MLFlow config uses postgresql://...
    and no storage mount if user picks 'POSTGRES'.
    """
    input_data = MLFlowAppInputs(
        preset=Preset(name="cpu-small"),
        ingress=Ingress(enabled=False, clusterName="test-cluster"),
        mlflow_specific=MLFlowSpecificInputs(
            http_auth=HttpAuthConfig(enabled=False),
            storage_backend=MLFlowStorageBackendConfig(
                backend=MLFlowStorageBackendEnum.POSTGRES
            ),
            postgres_app_name=PostgresAppNameConfig(name="pg-app"),
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

    # Check environment var for PG
    env_vars = helm_params["container"]["env"]
    tracking_env = next(
        (e for e in env_vars if e["name"] == "MLFLOW_TRACKING_URI"), None
    )
    assert tracking_env is not None
    assert "postgresql://pg-app.default/mlflow" in tracking_env["value"]

    # No storage injection
    pod_annot = helm_params.get("podAnnotations", {})
    assert "platform.apolo.us/inject-storage" not in pod_annot

    assert helm_params["labels"]["application"] == "mlflow"
