from urllib.parse import quote

import pytest


pytest.importorskip("pydantic")

from apolo_app_types.protocols.common import ApoloSecret
from apolo_app_types.protocols.resp_api import RESPApi


@pytest.mark.asyncio
async def test_no_credentials():
    r = RESPApi(host="localhost", port=6379)
    assert await r.resp_uri() == "redis://localhost:6379"


@pytest.mark.asyncio
async def test_plain_password_encoding_and_basepath():
    r = RESPApi(
        host="localhost", port=6379, user="u", password="p@ss:word", base_path="0"
    )
    expected_pw = quote("p@ss:word", safe="")
    assert await r.resp_uri() == f"redis://u:{expected_pw}@localhost:6379/0"


@pytest.mark.asyncio
async def test_secret_placeholder_encoded():
    secret = ApoloSecret(key="my-secret-key")
    r = RESPApi(host="redis", port=6379, user="u", password=secret, base_path="/cache")

    class FakeSecrets:
        async def get(self, key):
            assert key == secret.key
            return b"some-secret"

    class FakeClient:
        def __init__(self):
            self.secrets = FakeSecrets()

    pw_enc = quote("some-secret", safe="")
    assert (
        await r.resp_uri(client=FakeClient()) == f"redis://u:{pw_enc}@redis:6379/cache"
    )


@pytest.mark.asyncio
async def test_scheme_normalization():
    r1 = RESPApi(scheme="redis", host="redis", port=6379)
    r2 = RESPApi(scheme="redis://", host="redis", port=6379)
    assert await r1.resp_uri() == "redis://redis:6379"
    assert await r2.resp_uri() == "redis://redis:6379"


@pytest.mark.asyncio
async def test_secret_requires_client():
    secret = ApoloSecret(key="missing")
    r = RESPApi(host="redis", port=6379, user="u", password=secret, base_path="/cache")
    with pytest.raises(
        ValueError, match="client is required to resolve ApoloSecret password"
    ):
        await r.resp_uri()


@pytest.mark.asyncio
async def test_secret_not_found_mapping():
    import apolo_sdk

    secret = ApoloSecret(key="not-exist")
    r = RESPApi(host="redis", port=6379, user="u", password=secret, base_path="/cache")

    class FakeSecrets:
        async def get(self, key):
            assert key == secret.key
            msg = "no such secret"
            raise apolo_sdk.ResourceNotFound(msg)

    class FakeClient:
        def __init__(self):
            self.secrets = FakeSecrets()

    with pytest.raises(ValueError, match=f"secret not found: {secret.key}"):
        await r.resp_uri(client=FakeClient())
