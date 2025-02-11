import base64
from contextlib import AsyncExitStack
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apolo_sdk import AppsConfig


@pytest.fixture
async def setup_clients():
    from apolo_sdk import Bucket, BucketCredentials, PersistentBucketCredentials

    async with AsyncExitStack() as stack:
        with patch("apolo_sdk.get", return_value=AsyncMock()) as mock_get:
            mock_apolo_client = MagicMock()
            mock_cluster = MagicMock()
            mock_cluster.apps = AppsConfig(
                hostname_templates=["{app_names}.apps.some.org.neu.ro"]
            )
            mock_apolo_client.config.get_cluster = MagicMock(return_value=mock_cluster)
            mock_bucket = Bucket(
                id="bucket-id",
                owner="owner",
                cluster_name="cluster",
                org_name="test-org",
                project_name="test-project",
                provider=Bucket.Provider.GCP,
                created_at=datetime.today(),
                imported=False,
                name="test-bucket",
            )
            mock_apolo_client.buckets.get = AsyncMock(return_value=mock_bucket)
            p_credentials = PersistentBucketCredentials(
                id="cred-id",
                owner="owner",
                cluster_name="cluster",
                name="test-creds",
                read_only=False,
                credentials=[
                    BucketCredentials(
                        bucket_id="bucket-id",
                        provider=Bucket.Provider.GCP,
                        credentials={
                            "bucket_name": "test-bucket",
                            "key_data": base64.b64encode(b"bucket-access-key"),
                        },
                    )
                ],
            )
            mock_apolo_client.buckets.persistent_credentials_get = AsyncMock(
                return_value=p_credentials
            )

            mock_get.return_value.__aenter__.return_value = mock_apolo_client
            apolo_client = await stack.enter_async_context(mock_get())
            yield apolo_client
            await stack.aclose()


@pytest.fixture
def mock_get_preset_cpu():
    with (
        patch("apolo_app_types.helm.apps.common.get_preset") as mock,
        patch("apolo_app_types.helm.apps.llm.get_preset") as mock_llm,
        patch("apolo_app_types.helm.apps.stable_diffusion.get_preset") as mock_sd,
    ):
        from apolo_sdk import Preset

        def return_preset(_, preset_name):
            if preset_name == "cpu-large":
                return Preset(
                    credits_per_hour=Decimal("1.0"),
                    cpu=1.0,
                    memory=100,
                    available_resource_pool_names=("cpu_pool",),
                )

            return Preset(
                credits_per_hour=Decimal("1.0"),
                cpu=1.0,
                memory=100,
                available_resource_pool_names=("cpu_pool",),
            )

        mock.side_effect = return_preset
        mock_llm.side_effect = return_preset
        mock_sd.side_effect = return_preset

        yield mock


@pytest.fixture
def mock_get_preset_gpu():
    with (
        patch("apolo_app_types.helm.apps.common.get_preset") as mock,
        patch("apolo_app_types.helm.apps.llm.get_preset") as mock_llm,
        patch("apolo_app_types.helm.apps.stable_diffusion.get_preset") as mock_sd,
    ):
        from apolo_sdk import Preset

        def return_preset(_, preset_name):
            return Preset(
                credits_per_hour=Decimal("1.0"),
                cpu=1.0,
                memory=100,
                nvidia_gpu=1,
                available_resource_pool_names=("gpu_pool",),
            )

        mock.side_effect = return_preset
        mock_llm.side_effect = return_preset
        mock_sd.side_effect = return_preset
        yield mock
