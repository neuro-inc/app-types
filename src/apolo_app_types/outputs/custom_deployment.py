import logging
import typing as t

from apolo_app_types import CustomDeploymentOutputs
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import RestAPI


logger = logging.getLogger()


async def get_custom_deployment_outputs(
    helm_values: dict[str, t.Any],
) -> dict[str, t.Any]:
    host_port = await get_ingress_host_port(
        match_labels={"application": "custom-deployment"}
    )
    if not host_port:
        logger.info("No ingress found for custom deployment")
        return {}
    host, port = host_port
    outputs = CustomDeploymentOutputs(
        internal_web_app_url=RestAPI(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )
    )
    return outputs.model_dump()
