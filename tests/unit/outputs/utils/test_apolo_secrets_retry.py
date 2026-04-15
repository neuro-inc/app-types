"""Unit tests for apolo secrets retry behaviour.

Verifies that ``create_apolo_secret_with_retry`` retries on transient
errors and eventually returns a secret, and that it raises after the
maximum number of attempts.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from apolo_app_types.outputs.utils.apolo_secrets import (
    create_apolo_secret_with_retry,
)
from apolo_app_types.protocols.common import ApoloSecret


@pytest.mark.asyncio
async def test_create_with_retry_succeeds_after_retries(monkeypatch):
    """Should retry on failures and succeed when underlying create succeeds."""

    call_count = {"n": 0}

    async def fake_create(app_instance_id: str, key: str, value: str):
        call_count["n"] += 1
        # fail twice, succeed on third
        if call_count["n"] < 3:
            msg = "transient error"
            raise Exception(msg)
        return ApoloSecret(key=f"{key}-{app_instance_id}")

    # patch the underlying create to our fake implementation
    monkeypatch.setattr(
        "apolo_app_types.outputs.utils.apolo_secrets.create_apolo_secret",
        fake_create,
    )

    # avoid real sleeping to keep tests fast
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    result = await create_apolo_secret_with_retry(
        app_instance_id="app-1",
        key="k",
        value="v",
        max_attempts=5,
        base_delay_seconds=0.01,
    )

    assert call_count["n"] == 3
    assert isinstance(result, ApoloSecret)
    assert result.key == "k-app-1"


@pytest.mark.asyncio
async def test_create_with_retry_raises_after_max_attempts(monkeypatch):
    """Should raise the underlying exception after exhausting attempts."""

    call_count = {"n": 0}

    async def always_fail(app_instance_id: str, key: str, value: str):
        call_count["n"] += 1
        msg = "persistent failure"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "apolo_app_types.outputs.utils.apolo_secrets.create_apolo_secret",
        always_fail,
    )

    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    with pytest.raises(RuntimeError):
        await create_apolo_secret_with_retry(
            app_instance_id="app-1",
            key="k",
            value="v",
            max_attempts=3,
            base_delay_seconds=0.01,
        )

    # should have attempted exactly max_attempts times
    assert call_count["n"] == 3
