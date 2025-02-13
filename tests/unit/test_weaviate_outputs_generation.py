import pytest
from apolo_app_types.outputs.weaviate import get_weaviate_outputs


@pytest.mark.asyncio
async def test_output_values_weaviate(setup_clients, mock_kubernetes_client):
    res = await get_weaviate_outputs(
        {
            "nameOverride": "weaviate",
            "clusterApi": {
                "username": "admin",
                "password": "admin",
            },
            "ingress": {"enabled": True},
        }
    )
    assert res["auth"] == {
        "username": "admin",
        "password": "admin",
    }
    assert res["external_rest_endpoint"]
    assert res["external_rest_endpoint"]["host"] == "example.com"
    assert res["external_rest_endpoint"]["base_path"] == "/v1"
    assert res["external_rest_endpoint"]["protocol"] == "https"
    assert res["external_graphql_endpoint"]["host"] == "example.com"
    assert res["external_graphql_endpoint"]["base_path"] == "/v1/graphql"
    assert res["internal_graphql_endpoint"]["host"] == "weaviate.default-namespace"
    assert res["internal_grpc_endpoint"]["host"] == "weaviate-grpc.default-namespace"
    assert res["internal_grpc_endpoint"]["port"] == 443


@pytest.mark.asyncio
async def test_output_values_weaviate_without_cluster_creds(
    setup_clients, mock_kubernetes_client
):
    res = await get_weaviate_outputs(
        {
            "ingress": {"enabled": True},
        }
    )
    assert res["auth"] == {
        "username": "",
        "password": "",
    }
