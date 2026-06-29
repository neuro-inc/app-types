from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from apolo_sdk import Preset
from apolo_sdk._server_cfg import NvidiaGPUPreset

from apolo_app_types.helm.apps.common import (
    NVIDIA_MIG_KEY_PREFIX,
    get_preset,
    preset_to_resources,
)


def test_get_preset_raises_value_error_when_preset_not_found():
    client = MagicMock()
    client.config.cluster_name = "test-cluster"
    client.config.presets = {"gpu-small": MagicMock()}

    with pytest.raises(
        ValueError, match="Preset invalid not exist in cluster test-cluster"
    ):
        get_preset(client, "invalid")


def test_preset_to_resources_basic():
    """Test basic preset to resources conversion without GPUs."""
    preset = Preset(
        credits_per_hour=Decimal("1.0"),
        cpu=2.0,
        memory=4 * (1 << 20),  # 4 MB in bytes
        resource_pool_names=("default",),
        available_resource_pool_names=("default",),
    )

    result = preset_to_resources(preset)

    assert result == {
        "requests": {
            "cpu": "2000.0m",
            "memory": "4M",
        },
        "limits": {
            "cpu": "2000.0m",
            "memory": "4M",
        },
    }


def test_preset_to_resources_with_nvidia_gpu():
    """Test preset to resources conversion with NVIDIA GPU."""
    preset = Preset(
        credits_per_hour=Decimal("1.0"),
        cpu=4.0,
        memory=16 * (1 << 20),  # 16 MB in bytes
        nvidia_gpu=NvidiaGPUPreset(count=2),
        resource_pool_names=("gpu",),
        available_resource_pool_names=("gpu",),
    )

    result = preset_to_resources(preset)

    assert result == {
        "requests": {
            "cpu": "4000.0m",
            "memory": "16M",
            "nvidia.com/gpu": "2",
        },
        "limits": {
            "cpu": "4000.0m",
            "memory": "16M",
            "nvidia.com/gpu": "2",
        },
    }


def test_preset_to_resources_with_nvidia_mig_single_profile():
    """Test preset to resources conversion with a single NVIDIA MIG profile."""
    preset = Preset(
        credits_per_hour=Decimal("1.0"),
        cpu=8.0,
        memory=32 * (1 << 20),  # 32 MB in bytes
        nvidia_migs={
            "1g.5gb": NvidiaGPUPreset(count=2),
        },
        resource_pool_names=("mig",),
        available_resource_pool_names=("mig",),
    )

    result = preset_to_resources(preset)

    assert result["requests"]["cpu"] == "8000.0m"
    assert result["requests"]["memory"] == "32M"
    assert result["requests"][f"{NVIDIA_MIG_KEY_PREFIX}1g.5gb"] == "2"

    # Verify limits match requests
    assert result["limits"] == result["requests"]


def test_preset_to_resources_with_nvidia_mig_larger_profile():
    """Test preset to resources conversion with a larger NVIDIA MIG profile."""
    preset = Preset(
        credits_per_hour=Decimal("1.0"),
        cpu=16.0,
        memory=64 * (1 << 20),  # 64 MB in bytes
        nvidia_migs={
            "3g.20gb": NvidiaGPUPreset(count=1),
        },
        resource_pool_names=("mig",),
        available_resource_pool_names=("mig",),
    )

    result = preset_to_resources(preset)

    # Verify the MIG profile is included
    assert result["requests"][f"{NVIDIA_MIG_KEY_PREFIX}3g.20gb"] == "1"
    assert result["requests"]["cpu"] == "16000.0m"
    assert result["requests"]["memory"] == "64M"

    # Verify limits match requests
    assert result["limits"] == result["requests"]


def test_preset_to_resources_with_empty_nvidia_migs():
    """Test preset to resources conversion with empty nvidia_migs dict."""
    preset = Preset(
        credits_per_hour=Decimal("1.0"),
        cpu=2.0,
        memory=4 * (1 << 20),  # 4 MB in bytes
        nvidia_migs={},
        resource_pool_names=("default",),
        available_resource_pool_names=("default",),
    )

    result = preset_to_resources(preset)

    # Empty nvidia_migs should not add any MIG resources
    assert "nvidia.com/gpu" not in result["requests"]
    assert not any(
        key.startswith(NVIDIA_MIG_KEY_PREFIX) for key in result["requests"].keys()
    )
