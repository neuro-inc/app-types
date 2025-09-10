import pytest

from apolo_app_types.outputs.dify import get_dify_outputs


@pytest.mark.asyncio
async def test_dify(setup_clients, mock_kubernetes_client, app_instance_id):
    res = await get_dify_outputs(helm_values={}, app_instance_id=app_instance_id)

    assert res["app_url"]["internal_url"]["host"] == "app.default-namespace"
    assert res["app_url"]["internal_url"]["port"] == 80

    assert res["app_url"]["external_url"]["host"] == "example.com"
    assert res["app_url"]["external_url"]["port"] == 80


@pytest.mark.asyncio
async def test_dify_with_password(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    res = await get_dify_outputs(
        {
            "api": {"initPassword": "some_password"},
        },
        app_instance_id=app_instance_id,
    )

    assert res["app_url"]["internal_url"]["host"] == "app.default-namespace"
    assert res["app_url"]["internal_url"]["port"] == 80

    assert res["app_url"]["external_url"]["host"] == "example.com"
    assert res["app_url"]["external_url"]["port"] == 80

    assert res["dify_specific"]["init_password"] == "some_password"

    assert res["api_url"]["internal_url"]["host"] == "app.default-namespace"
    assert res["api_url"]["internal_url"]["port"] == 80
    assert res["api_url"]["external_url"]["host"] == "example.com"
    assert res["api_url"]["external_url"]["port"] == 80
