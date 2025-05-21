import typing as t

from apolo_app_types import MLFlowAppOutputs, MLFlowTrackingServerURL
from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import get_internal_external_web_urls
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port


async def get_mlflow_outputs(
    helm_values: dict[str, t.Any],
) -> dict[str, t.Any]:
    labels = {"application": "mlflow"}
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )

    # Get internal server URL
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_server_url = None
    if internal_host:
        internal_server_url = MLFlowTrackingServerURL(
            host=internal_host,
            port=int(internal_port),
            protocol="http",
        )

    # Get external server URL
    external_server_url = None
    ingress_host_port = await get_ingress_host_port(match_labels=labels)
    if ingress_host_port:
        external_server_url = MLFlowTrackingServerURL(
            host=ingress_host_port[0],
            port=int(ingress_host_port[1]),
            protocol="https",
        )

    return MLFlowAppOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
        internal_server_url=internal_server_url,
        external_server_url=external_server_url,
    ).model_dump()
