import typing as t

from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import INSTANCE_LABEL
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common import ServiceAPI
from apolo_app_types.protocols.common.networking import WebApp
from apolo_app_types.protocols.superset import SupersetOutputs, SupersetUserConfig


async def get_superset_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    labels = {"application": "superset", INSTANCE_LABEL: app_instance_id}
    internal_host, internal_port = await get_service_host_port(match_labels=labels)
    internal_web_app_url = None
    if internal_host:
        internal_web_app_url = WebApp(
            host=internal_host,
            port=int(internal_port),
            base_path="/",
            protocol="http",
        )

    host_port = await get_ingress_host_port(match_labels=labels)
    external_web_app_url = None
    if host_port:
        host, port = host_port
        external_web_app_url = WebApp(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )
    admin_config = helm_values.get("init", {}).get("adminUser", {})
    return SupersetOutputs(
        app_url=ServiceAPI[WebApp](
            internal_url=internal_web_app_url,
            external_url=external_web_app_url,
        ),
        secret=helm_values.get("extraSecretEnv", {}).get("SUPERSET_SECRET_KEY", None),
        admin_user=SupersetUserConfig(
            username=admin_config.get("username"),
            firstname=admin_config.get("firstname"),
            lastname=admin_config.get("lastname"),
            password=admin_config.get("password"),
            email=admin_config.get("email"),
        ),
    ).model_dump()
