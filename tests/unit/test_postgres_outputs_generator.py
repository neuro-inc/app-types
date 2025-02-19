import pytest

from apolo_app_types.outputs.postgres import get_postgres_outputs


@pytest.mark.asyncio
async def test_sd(setup_clients, mock_kubernetes_client):
    res = await get_postgres_outputs(
        helm_values={}
    )

    assert res
    assert res["external_api"]["host"] == "example.com"
    assert res["external_api"]["base_path"] == "/sdapi/v1"
    assert res["internal_api"]["host"] == "app.default-namespace"
    assert res["internal_api"]["base_path"] == "/sdapi/v1"
    assert res["hf_model"] == {
        "modelHFName": "SD-Model",
        "modelFiles": "some_file",
        "hfToken": None,
    }
