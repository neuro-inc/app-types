import typing as t

from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import INSTANCE_LABEL
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import HttpApi, RestAPI, ServiceAPI
from apolo_app_types.protocols.launchpad import KeycloakConfig, LaunchpadAppOutputs


async def get_launchpad_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    labels = {
        "application": "launchpad",
        INSTANCE_LABEL: app_instance_id,
    }

    launchpad_labels = {
        **labels,
        "service": "launchpad",
    }
    internal_host, internal_port = await get_service_host_port(
        match_labels=launchpad_labels
    )
    internal_web_app_url = None
    if internal_host:
        internal_web_app_url = RestAPI(
            host=internal_host,
            port=int(internal_port),
            base_path="/",
            protocol="http",
        )

    host_port = await get_ingress_host_port(match_labels=launchpad_labels)
    external_web_app_url = None
    if host_port:
        host, port = host_port
        external_web_app_url = RestAPI(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )

    # keycloak urls
    keycloak_labels = {
        **labels,
        "service": "keycloak",
    }

    host_port = await get_ingress_host_port(match_labels=keycloak_labels)
    keycloak_external_web_app_url = None
    if host_port:
        host, port = host_port
        keycloak_external_web_app_url = RestAPI(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )

    internal_host, internal_port = await get_service_host_port(
        match_labels=keycloak_labels
    )
    keycloak_internal_web_app_url = None
    if internal_host:
        keycloak_internal_web_app_url = RestAPI(
            host=internal_host,
            port=int(internal_port),
            base_path="/",
            protocol="http",
        )

    keycloak_password = helm_values["keycloak"]["auth"]["adminPassword"]
    outputs = LaunchpadAppOutputs(
        web_app_url=ServiceAPI[HttpApi](
            internal_url=internal_web_app_url,
            external_url=external_web_app_url,
        ),
        keycloak_config=KeycloakConfig(
            web_app_url=ServiceAPI[HttpApi](
                internal_url=keycloak_internal_web_app_url,
                external_url=keycloak_external_web_app_url,
            ),
            auth_admin_password=keycloak_password,
        ),
    )
    return outputs.model_dump()
