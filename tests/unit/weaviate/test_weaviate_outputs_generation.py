import pytest

from apolo_app_types.outputs.weaviate import get_weaviate_outputs


@pytest.mark.asyncio
async def test_output_values_weaviate(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    res = await get_weaviate_outputs(
        {
            "nameOverride": "weaviate",
            "clusterApi": {
                "username": "admin",
                "password": "admin",
            },
            "ingress": {"enabled": True},
        },
        app_instance_id=app_instance_id,
    )
    assert res["auth"] == {
        "username": "admin",
        "password": "admin",
    }
    assert res["rest_endpoint"]
    assert res["rest_endpoint"]["external_url"]["host"] == "example.com"
    assert res["rest_endpoint"]["external_url"]["base_path"] == "/v1"
    assert res["rest_endpoint"]["external_url"]["protocol"] == "https"
    assert res["graphql_endpoint"]["external_url"]["host"] == "example.com"
    assert res["graphql_endpoint"]["external_url"]["base_path"] == "/v1/graphql"
    assert (
        res["graphql_endpoint"]["internal_url"]["host"] == "weaviate.default-namespace"
    )
    assert (
        res["grpc_endpoint"]["internal_url"]["host"]
        == "weaviate-grpc.default-namespace"
    )
    assert res["grpc_endpoint"]["internal_url"]["port"] == 443


@pytest.mark.asyncio
async def test_output_values_weaviate_without_cluster_creds(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    res = await get_weaviate_outputs(
        {
            "ingress": {"enabled": True},
        },
        app_instance_id=app_instance_id,
    )
    assert res["auth"] == {
        "username": "",
        "password": "",
    }
