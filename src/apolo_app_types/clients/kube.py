import logging
import typing
from pathlib import Path

from kubernetes import client, config  # type: ignore
from kubernetes.client.rest import ApiException  # type: ignore


logger = logging.getLogger(__name__)

SERVICE_ACC_NAMESPACE_FILE = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"


def get_current_namespace() -> str:
    """
    Retrieve the current namespace from the Kubernetes service account namespace file.
    """
    try:
        with Path.open(Path(SERVICE_ACC_NAMESPACE_FILE)) as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error("Namespace file not found. Are you running in a Kubernetes pod?")
        raise
    except Exception as e:
        err_msg = f"Error while reading namespace file: {e}"
        logger.error(err_msg)
        raise


async def get_ingresses_as_dict(label_selectors: str) -> dict[str, typing.Any]:
    try:
        config.load_incluster_config()

        networking_v1 = client.NetworkingV1Api()
        namespace = get_current_namespace()
        ingresses = networking_v1.list_namespaced_ingress(
            namespace=namespace, label_selector=label_selectors
        )

        return client.ApiClient().sanitize_for_serialization(ingresses)

    except ApiException as e:
        err_msg = (
            f"Exception when calling NetworkingV1Api->list_namespaced_ingress: {e}"
        )
        logger.error(err_msg)
        raise e


async def get_services_by_label(label_selectors: str) -> dict[str, typing.Any]:
    try:
        config.load_incluster_config()

        v1 = client.CoreV1Api()
        namespace = get_current_namespace()
        services = v1.list_namespaced_service(
            namespace=namespace, label_selector=label_selectors
        )

        return client.ApiClient().sanitize_for_serialization(services)

    except ApiException as e:
        err_msg = f"Exception when calling CoreV1Api->list_namespaced_service: {e}"
        logger.error(err_msg)
        raise e
