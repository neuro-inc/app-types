import typing as t

from apolo_app_types import MLFlowAppOutputs, MLFlowTrackingServerURL
from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import (
    INSTANCE_LABEL,
    get_internal_external_web_urls,
)
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import HttpApi, RestAPI, ServiceAPI


async def get_mlflow_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    labels = {"application": "mlflow", INSTANCE_LABEL: app_instance_id}
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )

    # Get internal server URL
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_server_url = None
    if internal_host:
        internal_server_url = RestAPI(
            host=internal_host,
            port=int(internal_port),
            protocol="http",
        )

    # Get external server URL
    external_server_url = None
    ingress_host_port = await get_ingress_host_port(match_labels=labels)
    if ingress_host_port:
        external_server_url = RestAPI(
            host=ingress_host_port[0],
            port=int(ingress_host_port[1]),
            protocol="https",
        )

    return MLFlowAppOutputs(
        web_app_url=ServiceAPI[HttpApi](
            internal_url=internal_web_app_url,
            external_url=external_web_app_url,
        ),
        server_url=MLFlowTrackingServerURL(
            internal_url=internal_server_url,
            external_url=external_server_url,
        ),
        registered_models=None,
    ).model_dump()
