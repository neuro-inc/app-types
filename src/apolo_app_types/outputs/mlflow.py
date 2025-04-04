# File: /src/apolo_app_types/outputs/mlflow.py

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

    internal_url = None
    service_result = await get_service_host_port(match_labels=labels)
    if service_result:
        host, port = service_result
        internal_url = RestAPI(
            host=host, port=int(port), protocol="http", base_path="/"
        )

    external_url = None
    ingress_result = await get_ingress_host_port(match_labels=labels)
    if ingress_result:
        host, port = ingress_result
        external_url = RestAPI(
            host=host, port=int(port), protocol="https", base_path="/"
        )

    return {
        "internal_web_app_url": internal_url,
        "external_web_app_url": external_url,
    }
