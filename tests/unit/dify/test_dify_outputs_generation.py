import pytest

from apolo_app_types.outputs.dify import get_dify_outputs


@pytest.mark.asyncio
async def test_dify(setup_clients, mock_kubernetes_client):
    res = await get_dify_outputs({})

    assert res["internal_web_app_url"]["host"] == "app.default-namespace"
    assert res["internal_web_app_url"]["port"] == 80

    assert res["external_web_app_url"]["host"] == "example.com"
    assert res["external_web_app_url"]["port"] == 80


@pytest.mark.asyncio
async def test_dify_with_password(setup_clients, mock_kubernetes_client):
    res = await get_dify_outputs(
        {
            "api": {"initPassword": "some_password"},
        }
    )

    assert res["internal_web_app_url"]["host"] == "app.default-namespace"
    assert res["internal_web_app_url"]["port"] == 80

    assert res["external_web_app_url"]["host"] == "example.com"
    assert res["external_web_app_url"]["port"] == 80

    assert res["dify_specific"]["init_password"] == "some_password"

    assert res["internal_api_url"]["host"] == "app.default-namespace"
    assert res["internal_api_url"]["port"] == 80
    assert res["external_api_url"]["host"] == "example.com"
    assert res["external_api_url"]["port"] == 80
