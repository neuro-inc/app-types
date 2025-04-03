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
    Inspect K8s Services/Ingress for the app with 'application=mlflow'.
    Return a dictionary with 'internal_web_app_url' and 'external_web_app_url'.
    """
    if labels is None:
        labels = {"application": "mlflow"}

    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_url = None
    if internal_host and internal_port:
        internal_url = RestAPI(
            host=internal_host, port=int(internal_port), protocol="http", base_path="/"
        )

    external_url = None
    ingress = await get_ingress_host_port(match_labels=labels)
    if ingress:
        host, port = ingress
        external_url = RestAPI(
            host=host, port=int(port), protocol="https", base_path="/"
        )

    return {
        "internal_web_app_url": internal_url,
        "external_web_app_url": external_url,
    }
