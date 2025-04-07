import logging
import typing as t

from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import RestAPI


logger = logging.getLogger(__name__)


async def get_mlflow_outputs(
    helm_values: dict[str, t.Any], labels: dict[str, str] | None = None
) -> dict[str, t.Any]:
    """
    Gather internal & external MLFlow URLs from K8s resources
    with label 'application=mlflow'.
    """
    if labels is None:
        labels = {"application": "mlflow"}

    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_url = None
    if internal_host:
        internal_url = RestAPI(
            host=internal_host,
            port=int(internal_port),
            protocol="http",
            base_path="/",
        )

    ingress_host_port = await get_ingress_host_port(match_labels=labels)
    external_url = None
    if ingress_host_port:
        external_url = RestAPI(
            host=ingress_host_port[0],
            port=int(ingress_host_port[1]),
            protocol="https",
            base_path="/",
        )

    return {
        "internal_web_app_url": internal_url,
        "external_web_app_url": external_url,
    }
