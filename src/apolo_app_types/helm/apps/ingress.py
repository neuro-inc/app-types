import re
import typing as t

import apolo_sdk
from yarl import URL

from apolo_app_types.protocols.common import IngressGrpc, IngressHttp
from apolo_app_types.protocols.common.k8s import Port


DOMAIN_SECTION_MAX_LENGTH = 63

APP_NAME_PLACEHOLDER = "app_name"
APP_NAME_F_STRING_EXPRESSION = f"{{{APP_NAME_PLACEHOLDER}}}"
F_STRING_EXPRESSION_RE = re.compile(r"\{.+?\}")


def _get_forward_auth_address(client: apolo_sdk.Client) -> URL:
    return client.config.api_url.with_path("/oauth/authorize")


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
    namespace: str,
    port_configurations: list[Port] | None = None,
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
    if not port_configurations:
        paths = [{"path": "/", "pathType": "Prefix", "portName": "http"}]
    else:
        paths = [
            {
                "path": port.path,
                "pathType": "Prefix",
                "portName": port.name,
            }
            for port in port_configurations
        ]
    return {
        "enabled": True,
        "className": "traefik",
        "hosts": [
            {
                "host": hostname,
                "paths": paths,
            }
        ],
    }


async def get_ingress_values(
    apolo_client: apolo_sdk.Client,
    ingress_http: IngressHttp | None,
    ingress_grpc: IngressGrpc | None,
    namespace: str,
    port_configurations: list[Port] | None = None,
) -> dict[str, t.Any]:
    # Initialize with disabled state
    ingress_vals: dict[str, t.Any] = {
        "ingress": {
            "enabled": False,
            "grpc": {"enabled": False},
            "annotations": {},
        }
    }
    http_configured = False
    grpc_configured = False

    # Process HTTP only if ingress_http object is provided
    if ingress_http:  # Check for presence instead of ingress_http.enabled
        http_configured = True
        http_ingress_config = await _generate_ingress_config(
            apolo_client, namespace, port_configurations
        )
        # Update only relevant http fields, keep base structure
        ingress_vals["ingress"].update(http_ingress_config)
        # Handle http_auth based on its presence in the input object
        if ingress_http.http_auth:
            forward_auth_name = "forwardauth"
            forward_auth_config = {
                "enabled": True,
                "name": forward_auth_name,
                "address": str(_get_forward_auth_address(apolo_client)),
                "trustForwardHeader": True,
            }
            ingress_vals["ingress"]["forwardAuth"] = forward_auth_config
            ingress_vals["ingress"].setdefault(
                "annotations", {}
            )  # Ensure annotations key exists
            ingress_vals["ingress"]["annotations"][
                "traefik.ingress.kubernetes.io/router.middlewares"
            ] = f"{namespace}-{forward_auth_name}@kubernetescrd"

    # Process gRPC only if ingress_grpc object is provided
    if ingress_grpc:  # Check for presence (assuming IngressGrpc was also changed)
        grpc_configured = True
        grpc_ingress_config = await _generate_ingress_config(
            apolo_client, namespace, port_configurations, namespace_suffix="-grpc"
        )
        # Update only the grpc sub-section
        ingress_vals["ingress"]["grpc"] = {
            "enabled": True,
            "className": "traefik",
            "hosts": grpc_ingress_config["hosts"],
            "annotations": {
                "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
                "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
            },
        }
        if ingress_grpc.http_auth:
            forward_auth_name = "forwardauth"
            ingress_vals["ingress"]["grpc"]["auth"] = {
                "enabled": True,
                "name": forward_auth_name,
                "address": str(_get_forward_auth_address(apolo_client)),
                "trustForwardHeader": True,
            }
        ingress_vals["ingress"]["grpc"].setdefault("annotations", {})
        ingress_vals["ingress"]["grpc"]["annotations"][
            "traefik.ingress.kubernetes.io/router.middlewares"
        ] = f"{namespace}-{forward_auth_name}@kubernetescrd"

    # Set the overall ingress enabled flag if either http or grpc was configured
    if http_configured or grpc_configured:
        ingress_vals["ingress"]["enabled"] = True
    # If neither is configured, the initial ingress_vals with enabled=False is returned

    return ingress_vals
