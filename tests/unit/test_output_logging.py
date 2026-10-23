import logging
from typing import Any

import pytest

from apolo_app_types import AppOutputs
from apolo_app_types.outputs.base import BaseAppOutputsProcessor


class ProcessorOutputs(AppOutputs):
    result: str


class OutputProcessor(BaseAppOutputsProcessor[ProcessorOutputs]):
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, Any], str]] = []

    async def _generate_outputs(
        self, helm_values: dict[str, Any], app_instance_id: str
    ) -> ProcessorOutputs:
        self.calls.append((helm_values, app_instance_id))
        return ProcessorOutputs(result="generated-output")


class FailingOutputProcessor(BaseAppOutputsProcessor[ProcessorOutputs]):
    async def _generate_outputs(
        self, helm_values: dict[str, Any], app_instance_id: str
    ) -> ProcessorOutputs:
        message = "synthetic-error-secret"
        raise RuntimeError(message)


async def test_output_logging_excludes_helm_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret = "synthetic-session-secret"
    values = {
        "frontend": {"sessionSecret": secret},
        "password": "synthetic-password",
        "APOLO_PASSED_CONFIG": "synthetic-platform-credentials",
    }
    processor = OutputProcessor()
    with caplog.at_level(logging.DEBUG, logger="apolo_app_types.outputs.base"):
        outputs = await processor.generate_outputs(values, "test-instance")
    assert processor.calls == [(values, "test-instance")]
    assert outputs == {"app_url": None, "result": "generated-output"}
    assert "test-instance" in caplog.text
    assert "OutputProcessor" in caplog.text
    assert "3 Helm fields" in caplog.text
    assert "Generated 2 output fields" in caplog.text
    assert "seconds" in caplog.text
    assert secret not in caplog.text
    assert "synthetic-password" not in caplog.text
    assert "synthetic-platform-credentials" not in caplog.text
    assert "sessionSecret" not in caplog.text
    assert "generated-output" not in caplog.text


async def test_failed_output_generation_does_not_log_completion_or_error_contents(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with (
        caplog.at_level(logging.DEBUG, logger="apolo_app_types.outputs.base"),
        pytest.raises(RuntimeError, match="synthetic-error-secret"),
    ):
        await FailingOutputProcessor().generate_outputs({}, "test-instance")
    assert "Generating outputs for App instance test-instance" in caplog.text
    assert "FailingOutputProcessor" in caplog.text
    assert "Generated " not in caplog.text
    assert "synthetic-error-secret" not in caplog.text
