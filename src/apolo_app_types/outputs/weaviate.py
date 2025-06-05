import logging
import typing as t

from apolo_app_types import (
    BasicAuth,
    WeaviateOutputs,
)
from apolo_app_types.clients.kube import get_services
from apolo_app_types.outputs.common import INSTANCE_LABEL
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import GraphQLAPI, GrpcAPI, RestAPI


logger = logging.getLogger()


async def _get_service_endpoints(
    release_name: str, app_instance_id: str
) -> tuple[tuple[str, int], tuple[str, int]]:
    services = await get_services(
        match_labels={
            "application": release_name,
            INSTANCE_LABEL: app_instance_id,
        }
    )
    http_host, grpc_host = "", ""
    http_port, grpc_port = 0, 0
    for service in services:
        service_name = service["metadata"]["name"]
        host = f"{service_name}.{service['metadata']['namespace']}"
        port = int(service["spec"]["ports"][0]["port"])  # Ensure port is int

        if service_name == "weaviate":
            http_host, http_port = host, port
        elif service_name == "weaviate-grpc":
            grpc_host, grpc_port = host, port

    if http_host == "" or grpc_host == "":
        msg = "Could not find both weaviate and weaviate-grpc services."
        raise Exception(msg)

    return (http_host, http_port), (grpc_host, grpc_port)


async def get_weaviate_outputs(
    helm_values: dict[str, t.Any], app_instance_id: str
) -> dict[str, t.Any]:
    release_name = "weaviate"
    cluster_api = helm_values.get("clusterApi", {})

    try:
        (http_host, http_port), (grpc_host, grpc_port) = await _get_service_endpoints(
            release_name, app_instance_id
        )
    except Exception as e:
        msg = f"Could not find Weaviate services: {e}"
        raise Exception(msg) from e

    internal_http_host = http_host if http_host else ""
    graphql_internal = GraphQLAPI(
        host=internal_http_host, base_path="/v1/graphql", protocol="http"
    )
    rest_internal = RestAPI(host=internal_http_host, base_path="/v1", protocol="http")
    grpc_internal = GrpcAPI(host=grpc_host, port=grpc_port, protocol="http")
    ingress_config = helm_values.get("ingress", {})
    # grpc_external = None
    rest_external = None
    graphql_external = None
    if ingress_config.get("enabled"):
        ingress_host_port = await get_ingress_host_port(
            match_labels={
                "application": "weaviate",
                INSTANCE_LABEL: app_instance_id,
            }
        )

        if ingress_host_port:
            base_external_host = ingress_host_port[0] if ingress_host_port[0] else ""
            graphql_external = GraphQLAPI(
                host=base_external_host,
                base_path="/v1/graphql",
                protocol="https",
                port=ingress_host_port[1],
            )
            rest_external = RestAPI(
                host=base_external_host,
                base_path="/v1",
                protocol="https",
                port=ingress_host_port[1],
            )

    auth = BasicAuth(
        username=cluster_api.get("username", ""),
        password=cluster_api.get("password", ""),
    )

    return WeaviateOutputs(
        external_graphql_endpoint=graphql_external,
        internal_graphql_endpoint=graphql_internal,
        external_rest_endpoint=rest_external,
        internal_rest_endpoint=rest_internal,
        # TODO: disabled for now till we fix grpc
        # external_grpc_endpoint=grpc_external,
        internal_grpc_endpoint=grpc_internal,
        auth=auth,
    ).model_dump()
