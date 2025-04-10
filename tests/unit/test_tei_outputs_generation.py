import pytest

from apolo_app_types.outputs.tei import get_tei_outputs


@pytest.mark.asyncio
async def test_tei_outputs(setup_clients, mock_kubernetes_client):
    res = await get_tei_outputs(
        helm_values={}
    )

    assert res["internal_api"]["host"] == "app.default-namespace"
    assert res["internal_api"]["port"] == 80
    assert res["internal_api"]["endpoint_url"] == "/v1/embeddings"

    assert res["external_api"]["host"] == "example.com"
    assert res["external_api"]["port"] == 80
    assert res["external_api"]["endpoint_url"] == "/v1/embeddings"
