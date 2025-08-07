import re
import typing as t
from copy import deepcopy

import apolo_sdk

from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.common import IngressGrpc, IngressHttp
from apolo_app_types.protocols.common.k8s import Port


DOMAIN_SECTION_MAX_LENGTH = 63

APP_NAME_PLACEHOLDER = "app_name"
APP_NAME_F_STRING_EXPRESSION = f"{{{APP_NAME_PLACEHOLDER}}}"
F_STRING_EXPRESSION_RE = re.compile(r"\{.+?\}")

# Middleware names
PROD_AUTH_MIDDLEWARE = "platform-platform-ingress-auth@kubernetescrd"
DEV_AUTH_MIDDLEWARE = "platform-platform-control-plane-ingress-auth@kubernetescrd"
PROD_STRIP_HEADERS_MIDDLEWARE = "platform-platform-strip-headers@kubernetescrd"
DEV_STRIP_HEADERS_MIDDLEWARE = (
    "platform-platform-control-plane-strip-headers@kubernetescrd"
)

# App types that require strip headers middleware
STRIP_HEADERS_APP_TYPES = {AppType.Weaviate}

DEV_API_URL_DOMAIN = "api.dev.apolo.us"

MIDDLEWARE_ANNOTATION_KEY = "traefik.ingress.kubernetes.io/router.middlewares"


def _get_middlewares_annotation_value(app_type: AppType, *, is_production: bool) -> str:
    """Generate middleware string based on app type and cluster environment."""
    auth_middleware = PROD_AUTH_MIDDLEWARE if is_production else DEV_AUTH_MIDDLEWARE

    if app_type in STRIP_HEADERS_APP_TYPES:
        strip_headers_middleware = (
            PROD_STRIP_HEADERS_MIDDLEWARE
            if is_production
            else DEV_STRIP_HEADERS_MIDDLEWARE
        )
        return f"{auth_middleware},{strip_headers_middleware}"

    return auth_middleware


def is_production_cluster(client: apolo_sdk.Client) -> bool:
    return DEV_API_URL_DOMAIN not in str(client.config.api_url)


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
    app_id: str,
    app_type: AppType,
    port_configurations: list[Port] | None = None,
    namespace_suffix: str = "",
) -> dict[str, t.Any]:
    ingress_hostname = await _get_ingress_name_template(apolo_client)
    hostname = ingress_hostname.format(
        **{APP_NAME_PLACEHOLDER: f"{app_type.value}--{app_id}{namespace_suffix}"}
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
    app_id: str,
    app_type: AppType,
    port_configurations: list[Port] | None = None,
) -> dict[str, t.Any]:
    http_ingress_config = await _generate_ingress_config(
        apolo_client, app_id, app_type, port_configurations
    )
    ingress_vals: dict[str, t.Any] = {
        "enabled": True,
        **http_ingress_config,  # Merge the generated config directly
    }

    # Handle auth based on its presence in the input object
    if ingress_http.auth:
        ingress_vals.setdefault("annotations", {})  # Ensure annotations key exists
        is_prod = is_production_cluster(apolo_client)
        middleware_string = _get_middlewares_annotation_value(
            app_type, is_production=is_prod
        )
        ingress_vals["annotations"][MIDDLEWARE_ANNOTATION_KEY] = middleware_string

    return ingress_vals


async def get_grpc_ingress_values(
    apolo_client: apolo_sdk.Client,
    ingress_grpc: IngressGrpc,
    namespace: str,
    app_id: str,
    app_type: AppType,
    port_configurations: list[Port] | None = None,
) -> dict[str, t.Any]:
    grpc_ingress_config = await _generate_ingress_config(
        apolo_client,
        app_id,
        app_type,
        port_configurations,
        namespace_suffix="-grpc",
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
        grpc_vals.setdefault("annotations", {})
        is_prod = is_production_cluster(apolo_client)
        middleware_string = _get_middlewares_annotation_value(
            app_type, is_production=is_prod
        )
        grpc_vals["annotations"][MIDDLEWARE_ANNOTATION_KEY] = middleware_string

    return grpc_vals


async def append_ingress_middleware_annotations(
    current_annotations: dict[str, t.Any], namespace: str, middleware_name: str
) -> dict[str, t.Any]:
    curr_annot = deepcopy(current_annotations)

    middleware_annot = f"{namespace}-{middleware_name}@kubernetescrd"

    if MIDDLEWARE_ANNOTATION_KEY in curr_annot:
        curr_annot[MIDDLEWARE_ANNOTATION_KEY] += f",{middleware_annot}"
    else:
        curr_annot[MIDDLEWARE_ANNOTATION_KEY] = middleware_annot

    return curr_annot
