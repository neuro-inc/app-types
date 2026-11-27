from uuid import UUID

import pytest
from apolo_app_types_fixtures.constants import APP_ID, DEFAULT_NAMESPACE

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.ingress import (
    DOMAIN_SECTION_MAX_LENGTH,
    MIDDLEWARE_ANNOTATION_KEY,
    get_grpc_ingress_values,
    get_http_ingress_values,
)
from apolo_app_types.protocols.common import (
    ApoloAuth,
    CustomAuth,
    IngressGrpc,
    IngressHttp,
    NoAuth,
)
from apolo_app_types.protocols.common.middleware import AuthIngressMiddleware


PROD_API_URL = "https://api.apolo.us"
DEV_API_URL = "https://api.dev.apolo.us"
CUSTOM_AUTH = CustomAuth(
    middleware=AuthIngressMiddleware(name="platform-launchpad-auth"),
)

MIDDLEWARE_CASES = [
    pytest.param(
        ApoloAuth(),
        AppType.Triton,
        PROD_API_URL,
        "platform-platform-ingress-auth@kubernetescrd,"
        "platform-platform-token-filter@kubernetescrd",
        id="apolo-auth-prod",
    ),
    pytest.param(
        ApoloAuth(),
        AppType.Triton,
        DEV_API_URL,
        "platform-platform-control-plane-ingress-auth@kubernetescrd,"
        "platform-platform-control-plane-token-filter@kubernetescrd",
        id="apolo-auth-dev",
    ),
    pytest.param(
        ApoloAuth(),
        AppType.Weaviate,
        PROD_API_URL,
        "platform-platform-ingress-auth@kubernetescrd,"
        "platform-platform-strip-headers@kubernetescrd,"
        "platform-platform-token-filter@kubernetescrd",
        id="apolo-auth-strip-headers-prod",
    ),
    pytest.param(
        NoAuth(),
        AppType.Triton,
        PROD_API_URL,
        "platform-platform-token-filter@kubernetescrd",
        id="no-auth-prod",
    ),
    pytest.param(
        NoAuth(),
        AppType.Triton,
        DEV_API_URL,
        "platform-platform-control-plane-token-filter@kubernetescrd",
        id="no-auth-dev",
    ),
    pytest.param(
        CUSTOM_AUTH,
        AppType.Triton,
        PROD_API_URL,
        "platform-launchpad-auth@kubernetescrd,"
        "platform-platform-token-filter@kubernetescrd",
        id="custom-auth-prod",
    ),
    pytest.param(
        CUSTOM_AUTH,
        AppType.Triton,
        DEV_API_URL,
        "platform-launchpad-auth@kubernetescrd,"
        "platform-platform-control-plane-token-filter@kubernetescrd",
        id="custom-auth-dev",
    ),
]


@pytest.mark.asyncio
async def test_grpc_ingress_host_label_ends_with_app_id(setup_clients):
    values = await get_grpc_ingress_values(
        setup_clients,
        IngressGrpc(),
        DEFAULT_NAMESPACE,
        APP_ID,
        AppType.Triton,
    )

    host = values["hosts"][0]["host"]
    label = host.split(".", 1)[0]
    assert host == f"triton-grpc--{APP_ID}.apps.some.org.neu.ro"
    assert len(label) == 45
    assert len(label) <= DOMAIN_SECTION_MAX_LENGTH
    assert UUID(label.split("--", 1)[1]) == UUID(APP_ID)


@pytest.mark.asyncio
async def test_http_ingress_host_label_is_unchanged(setup_clients):
    values = await get_http_ingress_values(
        setup_clients,
        IngressHttp(),
        DEFAULT_NAMESPACE,
        APP_ID,
        AppType.Triton,
    )

    assert values["hosts"][0]["host"] == f"triton--{APP_ID}.apps.some.org.neu.ro"


@pytest.mark.asyncio
@pytest.mark.parametrize(("auth", "app_type", "api_url", "expected"), MIDDLEWARE_CASES)
async def test_http_ingress_middlewares_end_with_token_filter(
    setup_clients, auth, app_type, api_url, expected
):
    setup_clients.config.api_url = api_url

    values = await get_http_ingress_values(
        setup_clients,
        IngressHttp(auth=auth),
        DEFAULT_NAMESPACE,
        APP_ID,
        app_type,
    )

    assert values["annotations"] == {MIDDLEWARE_ANNOTATION_KEY: expected}


@pytest.mark.asyncio
@pytest.mark.parametrize(("auth", "app_type", "api_url", "expected"), MIDDLEWARE_CASES)
async def test_grpc_ingress_middlewares_end_with_token_filter(
    setup_clients, auth, app_type, api_url, expected
):
    setup_clients.config.api_url = api_url

    values = await get_grpc_ingress_values(
        setup_clients,
        IngressGrpc(auth=auth),
        DEFAULT_NAMESPACE,
        APP_ID,
        app_type,
    )

    assert values["annotations"] == {
        "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
        "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
        MIDDLEWARE_ANNOTATION_KEY: expected,
    }
