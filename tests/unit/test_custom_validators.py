import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from apolo_app_types.protocols.common.custom_validators import (
    CustomValidationError,
    validate_preset_custom_validator,
)


def _make_client(preset: object | None) -> MagicMock:
    client = MagicMock()
    client.config.presets = {"preset-a": preset}
    return client


def _gpu_preset(*, memory: int | None = None) -> SimpleNamespace:
    return SimpleNamespace(memory=memory)


def test_validate_preset_custom_validator_reports_missing_preset() -> None:
    errors = asyncio.run(
        validate_preset_custom_validator(
            {"name": "preset-a"},
            {"exists": True},
            cluster_name="test-cluster",
            path=["preset"],
            apolo_client=_make_client(None),
        )
    )

    assert len(errors) == 1
    assert isinstance(errors[0], CustomValidationError)
    assert errors[0].validator == "preset_validator"


@pytest.mark.parametrize(
    ("preset", "validator_config", "expected_message_part"),
    [
        (
            SimpleNamespace(
                cpu=2.0,
                memory=8 * (1 << 30),
                nvidia_gpu=None,
                amd_gpu=None,
                intel_gpu=None,
                nvidia_migs={},
            ),
            {"min_cpu_cores": 4},
            "CPU cores",
        ),
        (
            SimpleNamespace(
                cpu=4.0,
                memory=4 * (1 << 30),
                nvidia_gpu=None,
                amd_gpu=None,
                intel_gpu=None,
                nvidia_migs={},
            ),
            {"min_ram_gib": 8},
            "RAM",
        ),
        (
            SimpleNamespace(
                cpu=4.0,
                memory=8 * (1 << 30),
                nvidia_gpu=_gpu_preset(memory=8 * (1 << 30)),
                amd_gpu=None,
                intel_gpu=None,
                nvidia_migs={},
            ),
            {
                "min_vram_gib": 10,
                "exists": True,
            },
            "GPU memory",
        ),
    ],
)
def test_validate_preset_custom_validator_reports_resource_mismatch(
    preset: object,
    validator_config: dict[str, object],
    expected_message_part: str,
) -> None:
    errors = asyncio.run(
        validate_preset_custom_validator(
            {"name": "preset-a"},
            validator_config,
            cluster_name="test-cluster",
            path=["preset"],
            apolo_client=_make_client(preset),
        )
    )

    assert errors
    assert any(expected_message_part in error.message for error in errors)


def test_validate_preset_custom_validator_accepts_matching_preset() -> None:
    errors = asyncio.run(
        validate_preset_custom_validator(
            {"name": "preset-a"},
            {
                "exists": True,
                "min_cpu_cores": 2,
                "min_ram_gib": 4,
                "min_vram_gib": 2,
            },
            cluster_name="test-cluster",
            path=["preset"],
            apolo_client=_make_client(
                SimpleNamespace(
                    cpu=4.0,
                    memory=8 * (1 << 30),
                    amd_gpu=None,
                    intel_gpu=None,
                    nvidia_gpu=SimpleNamespace(memory=2 * (1 << 30)),
                    nvidia_migs={},
                )
            ),
        )
    )

    assert errors == []
