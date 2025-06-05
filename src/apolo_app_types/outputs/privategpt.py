import typing as t

from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import INSTANCE_LABEL
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common import RestAPI
from apolo_app_types.protocols.private_gpt import PrivateGPTAppOutputs


async def get_privategpt_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    labels = {
        "application": "privategpt",
        INSTANCE_LABEL: app_instance_id,
    }
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_web_app_url = None
    if internal_host:
        internal_web_app_url = RestAPI(
            host=internal_host,
            port=int(internal_port),
            base_path="/",
            protocol="http",
        )

    host_port = await get_ingress_host_port(match_labels=labels)
    external_web_app_url = None
    if host_port:
        host, port = host_port
        external_web_app_url = RestAPI(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )
    outputs = PrivateGPTAppOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
    )
    return outputs.model_dump()
