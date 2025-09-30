from decimal import Decimal

from apolo_sdk import Preset
from neuro_config_client import NvidiaGPUPreset

from apolo_app_types import CrunchyPostgresUserCredentials


CPU_POOL = "cpu_pool"
GPU_POOL = "gpu_pool"
DEFAULT_POOL = "default"
DEFAULT_NAMESPACE = "default"
DEFAULT_CLUSTER_NAME = "cluster"
DEFAULT_ORG_NAME = "test-org"
DEFAULT_PROJECT_NAME = "test-project"
APP_SECRETS_NAME = "apps-secrets"
APP_ID = "b1aeaf654526474ba22480d00e5b0109"

CPU_PRESETS = {
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
    "cpu-large": Preset(
        cpu=4.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=0),
        credits_per_hour=Decimal("0.1"),
        available_resource_pool_names=("cpu_pool",),
    ),
}


GPU_PRESETS = {
    "gpu-small": Preset(
        cpu=2.0,
        memory=8,
        nvidia_gpu=NvidiaGPUPreset(count=1, memory=2e9),
        credits_per_hour=Decimal("0.2"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "gpu-large": Preset(
        cpu=4.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=4, memory=2e9),
        credits_per_hour=Decimal("0.2"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "gpu-xlarge": Preset(
        cpu=8.0,
        memory=32,
        nvidia_gpu=NvidiaGPUPreset(count=8, memory=2e9),
        credits_per_hour=Decimal("0.4"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "a100-large": Preset(
        cpu=8.0,
        memory=32,
        nvidia_gpu=NvidiaGPUPreset(count=1, memory=80e9),
        credits_per_hour=Decimal("4"),
        available_resource_pool_names=("gpu_pool",),
    ),
    "t4-medium": Preset(
        cpu=2.0,
        memory=16,
        nvidia_gpu=NvidiaGPUPreset(count=1, memory=16e9),
        credits_per_hour=Decimal("0.1"),
        available_resource_pool_names=("gpu_pool",),
    ),
}

TEST_PRESETS = {
    **CPU_PRESETS,
    **GPU_PRESETS,
}

TEST_PRESETS_WITH_EXTRA_LARGE_GPU = {
    **TEST_PRESETS,
    "gpu-extra-large": Preset(
        cpu=16.0,
        memory=64,
        nvidia_gpu=NvidiaGPUPreset(count=3, memory=80e9),
        credits_per_hour=Decimal("8"),
        available_resource_pool_names=("gpu_pool",),
    ),
}


# OpenWebUI Test Constants
DEFAULT_AUTH_MIDDLEWARE = "platform-platform-control-plane-ingress-auth"
CUSTOM_AUTH_MIDDLEWARE = "platform-custom-auth-middleware"
CUSTOM_RATE_LIMITING_MIDDLEWARE = "platform-custom-rate-limiting-middleware"

DATABASE_SQLITE = "sqlite"
DATABASE_POSTGRES = "postgres"

# Default PostgreSQL credentials for testing
DEFAULT_POSTGRES_CREDS = CrunchyPostgresUserCredentials(
    user="pgvector_user",
    password="pgvector_password",
    host="pgvector_host",
    port=5432,
    pgbouncer_host="pgbouncer_host",
    pgbouncer_port=4321,
    dbname="db_name",
)
