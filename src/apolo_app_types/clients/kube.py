import logging
import os
import typing
from pathlib import Path

from kubernetes import client, config  # type: ignore
from kubernetes.client.rest import ApiException  # type: ignore


logger = logging.getLogger(__name__)

SERVICE_ACC_NAMESPACE_FILE = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
NAMESPACE_ENV_VAR = "APOLO_APP_NAMESPACE"


def get_current_namespace() -> str:
    """
    Retrieve the current namespace from the Kubernetes service account namespace file.
    """
    if NAMESPACE_ENV_VAR in os.environ:
        return os.environ[NAMESPACE_ENV_VAR]
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


async def get_services(match_labels: dict[str, str]) -> list[dict[str, typing.Any]]:
    label_selectors = ",".join(f"{k}={v}" for k, v in match_labels.items())
    get_svc_stdout = await get_services_by_label(label_selectors)

    return get_svc_stdout["items"]


async def get_service_host_port(match_labels: dict[str, str]) -> tuple[str, str]:
    services = await get_services(match_labels)
    if not services:
        msg = f"Service with labels {match_labels} not found"
        raise Exception(msg)
    if len(services) > 1:
        msg = f"Multiple services with labels {match_labels} found"
        logger.warning(msg)

    service = services[0]
    host = f"{service['metadata']['name']}.{service['metadata']['namespace']}"
    post = str(service["spec"]["ports"][0]["port"])

    return host, post


async def get_secret(label: str) -> typing.Any:
    try:
        config.load_incluster_config()

        v1 = client.CoreV1Api()
        namespace = get_current_namespace()

        return v1.list_namespaced_secret(
            namespace=namespace,
            label_selector=label,
        )

    except ApiException as e:
        err_msg = f"Exception when calling CoreV1Api->read_namespaced_secret: {e}"
        logger.error(err_msg)
        raise e


def get_crd_objects(
    *,
    api_group: str,
    api_version: str,
    crd_plural_name: str,
) -> dict[str, typing.Any]:
    config.load_incluster_config()

    namespace = get_current_namespace()
    api = client.CustomObjectsApi()
    return api.list_namespaced_custom_object(
        group=api_group,
        version=api_version,
        namespace=namespace,
        plural=crd_plural_name,
    )
