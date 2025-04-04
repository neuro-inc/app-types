import pytest

from apolo_app_types.outputs.mlflow import get_mlflow_outputs


@pytest.mark.asyncio
async def test_mlflow_outputs_generation(
    setup_clients, mock_kubernetes_client, monkeypatch
):
    """
    Validate that get_mlflow_outputs returns the correct
    internal/external URLs from K8s resources labeled application=mlflow.
    This works regardless of the storage backend (SQLite/Postgres) or
    artifact store configuration.
    """

    async def mock_get_service_host_port(*args, **kwargs):
        return ("mlflow-deploy.default.svc.cluster.local", 5000)

    async def mock_get_ingress_host_port(*args, **kwargs):
        return ("mlflow.example.com", 443)

    monkeypatch.setattr(
        "apolo_app_types.outputs.mlflow.get_service_host_port",
        mock_get_service_host_port,
    )
    monkeypatch.setattr(
        "apolo_app_types.outputs.mlflow.get_ingress_host_port",
        mock_get_ingress_host_port,
    )

    helm_values = {"labels": {"application": "mlflow"}}

    result = await get_mlflow_outputs(helm_values)
    assert result["internal_web_app_url"] is not None
    assert (
        result["internal_web_app_url"].host == "mlflow-deploy.default.svc.cluster.local"
    )
    assert result["internal_web_app_url"].port == 5000

    assert result["external_web_app_url"] is not None
    assert result["external_web_app_url"].host == "mlflow.example.com"
    assert result["external_web_app_url"].port == 443
