import base64
from contextlib import AsyncExitStack
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import apolo_sdk
import pytest
from apolo_sdk import AppsConfig
from yarl import URL
from .constants import DEFAULT_ORG_NAME, DEFAULT_CLUSTER_NAME, DEFAULT_PROJECT_NAME

@pytest.fixture
async def setup_clients(presets_available):
    from apolo_sdk import Bucket, BucketCredentials, PersistentBucketCredentials

    async with AsyncExitStack() as stack:
        with patch("apolo_sdk.get", return_value=AsyncMock()) as mock_get:
            mock_apolo_client = MagicMock()
            mock_cluster = MagicMock()
            mock_cluster.apps = AppsConfig(
                hostname_templates=["{app_names}.apps.some.org.neu.ro"]
            )
            mock_apolo_client.config.registry_url = PropertyMock(
                return_value="registry.cluster.org.neu.ro"
            )
            mock_apolo_client.config.api_url = "https://api.dev.apolo.us"
            mock_apolo_client.config.cluster_name = DEFAULT_CLUSTER_NAME
            mock_apolo_client.config.org_name = DEFAULT_ORG_NAME
            mock_apolo_client.config.project_name = DEFAULT_PROJECT_NAME

            mock_apolo_client.config.presets = presets_available

            mock_apolo_client.config.get_cluster = MagicMock(return_value=mock_cluster)
            mock_apolo_client.parse.remote_image = MagicMock(
                side_effect=lambda image, cluster_name: apolo_sdk.RemoteImage(
                    name=image,
                )
            )

            def parse_volume(volume):
                path = volume.replace("storage:", "")
                path, read_write = path.split(":")
                if path.startswith("//"):
                    full_path = volume
                elif path.startswith("/"):
                    path = path[1:]
                    full_path = (
                        f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{path}"
                    )
                else:
                    project = DEFAULT_PROJECT_NAME
                    full_path = f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{project}/{path}"
                return apolo_sdk.Volume(
                    storage_uri=URL(full_path),
                    container_path="/mock/storage",
                    read_only=False,
                )

            mock_apolo_client.parse.volume = MagicMock(side_effect=parse_volume)
            mock_apolo_client.username = PropertyMock(return_value="test-user")
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
                            "key_data": base64.b64encode(b"bucket-access-key").decode(),
                        },
                    )
                ],
            )
            mock_apolo_client.buckets.persistent_credentials_get = AsyncMock(
                return_value=p_credentials
            )
            mock_apolo_client.jobs.get_capacity = AsyncMock(
                return_value={
                    "cpu-large": 1,
                    "gpu-large": 1,
                    "gpu-xlarge": 1,
                    "a100-large": 1,
                    "cpu-small": 1,
                    "cpu-medium": 1,
                    "t4-medium": 1,
                    "gpu-extra-large": 1,
                },
            )

            mock_get.return_value.__aenter__.return_value = mock_apolo_client
            apolo_client = await stack.enter_async_context(mock_get())
            yield apolo_client
            await stack.aclose()

