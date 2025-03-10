import logging
import typing as t

from apolo_app_types import (
    HuggingFaceModel,
)
from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import RestAPI
from apolo_app_types.protocols.stable_diffusion import SDOutputsV2


logger = logging.getLogger()


async def get_stable_diffusion_outputs(
    helm_values: dict[str, t.Any],
) -> dict[str, t.Any]:
    internal_host, internal_port = await get_service_host_port(
        match_labels={"application": "stable-diffusion"}
    )
    ingress_host_port = await get_ingress_host_port(
        match_labels={"application": "stable-diffusion"}
    )
    if ingress_host_port:
        external_host = ingress_host_port[0]
    else:
        external_host = ""

    internal_api = RestAPI(
        host=internal_host,
        port=int(internal_port),
        base_path="/sdapi/v1",
        protocol="http",
    )
    external_api = RestAPI(
        host=external_host,
        base_path="/sdapi/v1",
        port=443,
        protocol="https",
    )
    model = HuggingFaceModel(modelHFName=helm_values["model"]["modelHFName"])
    stable_diffusion_output = SDOutputsV2(
        internal_api=internal_api, external_api=external_api, hf_model=model
    )

    return stable_diffusion_output.model_dump()
