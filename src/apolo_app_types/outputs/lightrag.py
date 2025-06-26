import typing as t

from apolo_app_types import LightRAGAppOutputs
from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import (
    INSTANCE_LABEL,
    get_internal_external_web_urls,
)
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import HttpApi, ServiceAPI


async def get_lightrag_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    """Generate LightRAG outputs"""
    # Use the full chart's label selector (app.kubernetes.io/name: lightrag)
    # and instance label for the deployed app
    labels = {"app.kubernetes.io/name": "lightrag", INSTANCE_LABEL: app_instance_id}

    # Get internal and external web app URLs using the common utility
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )

    # Get internal server URL (same as web app for LightRAG since it's a single service)
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_server_url = None
    if internal_host:
        internal_server_url = HttpApi(
            host=internal_host,
            port=int(internal_port),
            protocol="http",
        )

    # Get external server URL (same as web app for LightRAG)
    external_server_url = None
    ingress_host_port = await get_ingress_host_port(match_labels=labels)
    if ingress_host_port:
        external_server_url = HttpApi(
            host=ingress_host_port[0],
            port=int(ingress_host_port[1]),
            protocol="https",
        )

    return LightRAGAppOutputs(
        web_app_url=ServiceAPI[HttpApi](
            internal_url=internal_web_app_url,
            external_url=external_web_app_url,
        ),
        server_url=ServiceAPI[HttpApi](
            internal_url=internal_server_url,
            external_url=external_server_url,
        ),
    ).model_dump()
