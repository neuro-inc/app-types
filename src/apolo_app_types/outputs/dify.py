import typing as t

from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common import RestAPI
from apolo_app_types.protocols.dify import DifyAppOutputs, DifySpecificOutputs


async def get_dify_outputs(
    helm_values: dict[str, t.Any],
) -> dict[str, t.Any]:
    labels = {"application": "dify", "component": "api"}
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_web_app_url = None
    if internal_host:
        internal_web_app_url = RestAPI(
            host=internal_host,
            port=int(internal_port),
            base_path="/",
            protocol="http",
        )
    match_labels = {"application": "dify"}
    host_port = await get_ingress_host_port(match_labels=match_labels)
    external_web_app_url = None
    if host_port:
        host, port = host_port
        external_web_app_url = RestAPI(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )
    init_password = helm_values.get("api", {}).get("initPassword", "")
    outputs = DifyAppOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
        dify_specific=DifySpecificOutputs(
            init_password=init_password,
        )
    )
    return outputs.model_dump()