import pytest

from apolo_app_types.outputs.custom_deployment import get_custom_deployment_outputs


@pytest.mark.asyncio
async def test_custom_deployment_outputs_generation_with_ingress(
    setup_clients, mock_kubernetes_client, monkeypatch, app_instance_id: str
):
    async def mock_get_service_host_port(*args, **kwargs):
        return ("custom-deployment.default.svc.cluster.local", 80)

    monkeypatch.setattr(
        "apolo_app_types.outputs.common.get_service_host_port",
        mock_get_service_host_port,
    )

    async def mock_get_ingress_host_port(*args, **kwargs):
        return ("custom-deployment.example.com", 443)

    monkeypatch.setattr(
        "apolo_app_types.outputs.common.get_ingress_host_port",
        mock_get_ingress_host_port,
    )

    helm_values = {
        "image": {
            "repository": "myrepo/custom-deployment",
            "tag": "v1.0.0",
        },
    }
    res = await get_custom_deployment_outputs(
        helm_values=helm_values, app_instance_id=app_instance_id
    )
    assert res["external_web_app_url"]["host"] == "custom-deployment.example.com"
    assert res["external_web_app_url"]["port"] == 443

    assert (
        res["internal_web_app_url"]["host"]
        == "custom-deployment.default.svc.cluster.local"
    )
    assert res["internal_web_app_url"]["port"] == 80
