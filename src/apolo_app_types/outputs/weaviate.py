import logging
import typing as t

from apolo_app_types import (
    BasicAuth,
    WeaviateOutputs,
)
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.outputs.utils.parsing import get_service_host_port
from apolo_app_types.protocols.common.networking import GraphQLAPI, GrpcAPI, RestAPI


logger = logging.getLogger()


async def _get_service_endpoints(
    release_name: str,
) -> tuple[tuple[str, int], tuple[str, int]]:
    services = await get_service_host_port(
        match_labels={"app.kubernetes.io/name": release_name}
    )
    host, grpc_host = "", ""
    port, grpc_port = 0, 0
    for service in services:
        service_name = service["metadata"]["name"]
        host = f'{service_name}.{service["metadata"]["namespace"]}'
        port = int(service["spec"]["ports"][0]["port"])  # Ensure port is int

        if service_name == "weaviate":
            host, port = host, port
        elif service_name == "weaviate-grpc":
            grpc_host, grpc_port = host, port

    if host == "" or grpc_host == "":
        msg = "Could not find both weaviate and weaviate-grpc services."
        raise Exception(msg)

    return (host, port), (grpc_host, grpc_port)


async def get_weaviate_outputs(helm_values: dict[str, t.Any]) -> dict[str, t.Any]:
    release_name = helm_values.get("nameOverride", "weaviate")
    cluster_api = helm_values.get("clusterApi", {})

    try:
        (http_host, http_port), (grpc_host, grpc_port) = await _get_service_endpoints(
            release_name
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
    grpc_external = None
    rest_external = None
    graphql_external = None
    if ingress_config.get("enabled"):
        ingress_host_port = await get_ingress_host_port(
            match_labels={"application": "llm-inference"}
        )

        if ingress_host_port[0]:
            base_external_host = ingress_host_port[0] if ingress_host_port[0] else ""
            graphql_external = GraphQLAPI(
                host=base_external_host,
                base_path="/v1/graphql",
                protocol="https",
                port=int(ingress_host_port[1]),
            )
            rest_external = RestAPI(
                host=base_external_host,
                base_path="/v1",
                protocol="https",
                port=int(ingress_host_port[1]),
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
        external_grpc_endpoint=grpc_external,
        internal_grpc_endpoint=grpc_internal,
        auth=auth,
    ).model_dump()
