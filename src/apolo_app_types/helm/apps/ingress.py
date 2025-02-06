import re
import typing as t

import apolo_sdk
import click

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
        assert (
            len(re.findall(F_STRING_EXPRESSION_RE, template)) == 1
        ), "Invalid template"

        return re.sub(F_STRING_EXPRESSION_RE, APP_NAME_F_STRING_EXPRESSION, template)

    return f"{APP_NAME_F_STRING_EXPRESSION}.apps.{client.cluster_name}.org.neu.ro"


async def _generate_ingress_config(
    apolo_client: apolo_sdk.Client, namespace: str, namespace_suffix: str = ""
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
        raise click.ClickException(msg)
    return {
        "enabled": True,
        "className": "traefik",
        "hosts": [
            {
                "host": hostname,
                "paths": [{"path": "/", "pathType": "Prefix"}],
            }
        ],
    }


async def get_ingress_values(
    apolo_client: apolo_sdk.Client,
    ingress: Ingress,
    namespace: str,
) -> dict[str, t.Any]:
    ingress_vals: dict[str, t.Any] = {"ingress": {}}
    if ingress.enabled != "true":
        ingress_vals["ingress"]["enabled"] = False
        return ingress_vals

    ingress_vals["ingress"] = await _generate_ingress_config(apolo_client, namespace)
    return ingress_vals
