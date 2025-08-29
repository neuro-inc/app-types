import pytest

from apolo_app_types.outputs.shell import get_shell_outputs


@pytest.mark.asyncio
async def test_shell_outputs(setup_clients, mock_kubernetes_client, app_instance_id):
    res = await get_shell_outputs(helm_values={}, app_instance_id=app_instance_id)

    assert res["app_url"]["internal_url"]["host"] == "app.default-namespace"
    assert res["app_url"]["internal_url"]["port"] == 80
