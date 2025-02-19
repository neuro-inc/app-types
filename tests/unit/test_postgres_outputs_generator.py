import pytest

from apolo_app_types.outputs.postgres import get_postgres_outputs


@pytest.mark.asyncio
async def test_postgres_outputs(setup_clients, mock_kubernetes_client):
    res = await get_postgres_outputs(
        helm_values={}
    )
    assert res