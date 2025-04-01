import re
import typing as t

import apolo_sdk

from apolo_app_types.protocols.common import Ingress


DOMAIN_SECTION_MAX_LENGTH = 63

APP_NAME_PLACEHOLDER = "app_name"
APP_NAME_F_STRING_EXPRESSION = f"{{{APP_NAME_PLACEHOLDER}}}"
F_STRING_EXPRESSION_RE = re.compile(r"\{.+?\}")


async def _get_ingress_name_template(client: apolo_sdk.Client) -> str:
    cluster = client.config.get_cluster(client.config.cluster_name)
    apps_config = cluster.apps

    if apps_config.hostname_templates:
        # multi-domain clusters are not supported on the backend yet
        template = apps_config.hostname_templates[0]
        assert len(re.findall(F_STRING_EXPRESSION_RE, template)) == 1, (
            "Invalid template"
        )

        return re.sub(F_STRING_EXPRESSION_RE, APP_NAME_F_STRING_EXPRESSION, template)

    return f"{APP_NAME_F_STRING_EXPRESSION}.apps.{client.cluster_name}.org.neu.ro"


async def _generate_ingress_config(
    apolo_client: apolo_sdk.Client,
    ingress: Ingress,
    namespace: str,
    namespace_suffix: str = "",
) -> dict[str, t.Any]:
    ingress_hostname = await _get_ingress_name_template(apolo_client)
    hostname = ingress_hostname.format(
        **{APP_NAME_PLACEHOLDER: namespace + namespace_suffix}
    )

    if hostname.endswith("."):
        hostname = hostname[:-1]

    if any(
        len(hostname_part) > DOMAIN_SECTION_MAX_LENGTH
        for hostname_part in hostname.split(".")
    ):
        msg = (
            f"Generated hostname {hostname} is too long. "
            f"If your app name is long, consider using shorter app name."
        )
        raise Exception(msg)

    return {
        "enabled": True,
        "className": "traefik",
        "hosts": [
            {
                "host": hostname,
                "paths": [
                    {"path": _.path, "pathType": _.path_type, "portName": _.port_name}
                    for _ in ingress.paths
                ],
            }
        ],
    }


async def get_ingress_values(
    apolo_client: apolo_sdk.Client,
    ingress: Ingress,
    namespace: str,
) -> dict[str, t.Any]:
    ingress_vals: dict[str, t.Any] = {"ingress": {"grpc": {"enabled": False}}}
    if not ingress.enabled:
        ingress_vals["ingress"]["enabled"] = False
        return ingress_vals

    res = await _generate_ingress_config(apolo_client, ingress, namespace)
    ingress_vals["ingress"].update(res)
    if ingress.grpc and ingress.grpc.enabled:
        grpc_ingress_config = await _generate_ingress_config(
            apolo_client, ingress, namespace, namespace_suffix="-grpc"
        )
        ingress_vals["ingress"]["grpc"] = {
            "enabled": True,
            "className": "traefik",
            "hosts": grpc_ingress_config["hosts"],
            "annotations": {
                "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
                "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
            },
        }
    return ingress_vals
