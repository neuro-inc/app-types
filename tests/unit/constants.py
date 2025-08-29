from decimal import Decimal

from apolo_sdk import Preset
from neuro_config_client import NvidiaGPUPreset


CPU_POOL = "cpu_pool"
GPU_POOL = "gpu_pool"
DEFAULT_POOL = "default"
DEFAULT_NAMESPACE = "default"
DEFAULT_CLUSTER_NAME = "cluster"
DEFAULT_ORG_NAME = "test-org"
DEFAULT_PROJECT_NAME = "test-project"
APP_SECRETS_NAME = "apps-secrets"
APP_ID = "b1aeaf654526474ba22480d00e5b0109"

TEST_PRESETS = {
    "cpu-large": Preset(
        cpu=4.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=0),
        credits_per_hour=Decimal("0.1"),
        available_resource_pool_names=("cpu_pool",),
    ),
    "gpu-large": Preset(
        cpu=4.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=4),
        credits_per_hour=Decimal("0.2"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "gpu-xlarge": Preset(
        cpu=8.0,
        memory=32,
        nvidia_gpu=NvidiaGPUPreset(count=8),
        credits_per_hour=Decimal("0.4"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "a100-large": Preset(
        cpu=8.0,
        memory=32,
        nvidia_gpu=NvidiaGPUPreset(count=1, memory=16),
        credits_per_hour=Decimal("0.3"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "cpu-small": Preset(
        cpu=2.0,
        memory=8,
        nvidia_gpu=NvidiaGPUPreset(count=0),
        credits_per_hour=Decimal("0.05"),
        available_resource_pool_names=("cpu_pool",),
    ),
    "cpu-medium": Preset(
        cpu=2.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=0),
        credits_per_hour=Decimal("0.08"),
        available_resource_pool_names=("cpu_pool",),
    ),
    "t4-medium": Preset(
        cpu=2.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=1),
        credits_per_hour=Decimal("0.1"),
        available_resource_pool_names=("gpu_pool",),
    ),
}

TEST_PRESETS_WITH_EXTRA_LARGE_GPU = {
    **TEST_PRESETS,
    "gpu-extra-large": Preset(
        cpu=16.0,
        memory=64,
        nvidia_gpu=NvidiaGPUPreset(count=3, memory=80),
        credits_per_hour=Decimal("0.8"),
        available_resource_pool_names=("gpu_pool",),
    ),
}
