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


async def get_http_ingress_values(
    apolo_client: apolo_sdk.Client,
    ingress_http: IngressHttp,
    namespace: str,
    port_configurations: list[Port] | None = None,
) -> dict[str, t.Any]:
    http_ingress_config = await _generate_ingress_config(
        apolo_client, namespace, port_configurations
    )
    ingress_vals: dict[str, t.Any] = {
        "enabled": True,
        **http_ingress_config,  # Merge the generated config directly
    }

    # Handle auth based on its presence in the input object
    if ingress_http.auth:
        forward_auth_name = "forwardauth"
        forward_auth_config = {
            "enabled": True,
            "name": forward_auth_name,
            "address": str(_get_forward_auth_address(apolo_client)),
            "trustForwardHeader": True,
            "authResponseHeaders": [],
        }
        ingress_vals["forwardAuth"] = forward_auth_config
        ingress_vals.setdefault("annotations", {})  # Ensure annotations key exists
        ingress_vals["annotations"][
            "traefik.ingress.kubernetes.io/router.middlewares"
        ] = (
            f"{namespace}-{forward_auth_name}@kubernetescrd,"
            f"{namespace}-strip-headers@kubernetescrd"
        )

    return ingress_vals


async def get_grpc_ingress_values(
    apolo_client: apolo_sdk.Client,
    ingress_grpc: IngressGrpc,
    namespace: str,
    port_configurations: list[Port] | None = None,
) -> dict[str, t.Any]:
    grpc_ingress_config = await _generate_ingress_config(
        apolo_client, namespace, port_configurations, namespace_suffix="-grpc"
    )
    grpc_vals: dict[str, t.Any] = {
        "enabled": True,
        "className": "traefik",
        "hosts": grpc_ingress_config["hosts"],
        "annotations": {
            "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
            "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
        },
    }

    if ingress_grpc.auth:
        forward_auth_name = "forwardauth"
        grpc_vals["auth"] = {
            "enabled": True,
            "name": forward_auth_name,
            "address": str(_get_forward_auth_address(apolo_client)),
            "trustForwardHeader": True,
            "authResponseHeaders": [],
        }
        grpc_vals.setdefault("annotations", {})
        grpc_vals["annotations"]["traefik.ingress.kubernetes.io/router.middlewares"] = (
            f"{namespace}-{forward_auth_name}@kubernetescrd,{namespace}-strip-headers@kubernetescrd"
        )

    return grpc_vals
