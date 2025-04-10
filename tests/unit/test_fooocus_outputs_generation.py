import pytest
from apolo_app_types.outputs.fooocus import get_fooocus_outputs



@pytest.mark.asyncio
async def test_fooocus_outputs(setup_clients, mock_kubernetes_client):
    res = await get_fooocus_outputs(
        helm_values={}
    )

    assert res["internal_web_app_url"]["host"] == "app.default-namespace"
    assert res["internal_web_app_url"]["port"] == 80

    assert res["external_web_app_url"]["host"] == "example.com"
    assert res["external_web_app_url"]["port"] == 80
