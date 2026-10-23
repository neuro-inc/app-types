import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from apolo_app_types import AppOutputs
from apolo_app_types.outputs.base import BaseAppOutputsProcessor


class OutputProcessor(BaseAppOutputsProcessor[AppOutputs]):
    async def _generate_outputs(
        self, helm_values: dict[str, Any], app_instance_id: str
    ) -> AppOutputs:
        return AppOutputs()


async def test_output_logging_excludes_helm_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret = "synthetic-session-secret"
    values = {"frontend": {"sessionSecret": secret}, "password": "synthetic-password"}
    processor = OutputProcessor()
    with (
        caplog.at_level(logging.INFO),
        patch.object(
            processor, "_generate_outputs", new=AsyncMock(return_value=AppOutputs())
        ) as generate,
    ):
        outputs = await processor.generate_outputs(values, "test-instance")
    generate.assert_awaited_once_with(values, "test-instance")
    assert outputs == AppOutputs().model_dump()
    assert "test-instance" in caplog.text
    assert secret not in caplog.text
    assert "synthetic-password" not in caplog.text
    assert "sessionSecret" not in caplog.text
