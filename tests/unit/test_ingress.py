from uuid import UUID

import pytest
from apolo_app_types_fixtures.constants import APP_ID, DEFAULT_NAMESPACE

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.ingress import (
    DOMAIN_SECTION_MAX_LENGTH,
    get_grpc_ingress_values,
    get_http_ingress_values,
)
from apolo_app_types.protocols.common import IngressGrpc, IngressHttp


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
