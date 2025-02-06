import base64
from contextlib import AsyncExitStack
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apolo_sdk import AppsConfig


# from mlops_deployer._kube_config import read_kube_config as original_read_kube_config
#
#
# encoded_certificate_data = base64.b64encode(b"dummy cert data").decode("utf-8")
#
#
# MOCK_KUBECONFIG_CONTENT = f"""
# apiVersion: v1
# kind: Config
# clusters:
# - cluster:
#     certificate-authority-data: {encoded_certificate_data}
#     server: https://mock-cluster.example.com
#   name: mock-cluster
# contexts:
# - context:
#     cluster: mock-cluster
#     namespace: default
#     user: mock-user
#   name: mock-context
# current-context: mock-context
# preferences: {{}}
# users:
# - name: mock-user
#   user:
#     token: mock-token
# """
#
#
# @pytest.fixture(scope="session", autouse=True)
# def mock_read_kube_config(tmp_path_factory):
#     temp_file = tmp_path_factory.mktemp("kube") / "mock_kubeconfig.yaml"
#     temp_file.write_text(MOCK_KUBECONFIG_CONTENT)
#
#     import mlops_deployer._kube_config
#
#     mlops_deployer._kube_config.read_kube_config = (
#         lambda path=temp_file: original_read_kube_config(path=path)
#     )
#
#     return temp_file
#


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


#
# @pytest.fixture
# def mock_get_dify_pg_values():
#     with patch(
#         "mlops_deployer.helm.apps.dify._get_dify_pg_values",
#         new_callable=AsyncMock,
#     ) as mock:
#         # Set the return value to a mock CrunchyPostgresOutputs instance
#         mock.return_value = {
#             "externalPostgres": {
#                 "user": "user1",
#                 "password": "password1",
#                 "host": "host1",
#                 "port": "5555",
#                 "pgbouncer_host": "pgbouncer_host1",
#                 "pgbouncer_port": "5555",
#                 "dbname": "dbname1",
#             },
#             "externalPgvector": {
#                 "user": "user1",
#                 "password": "password1",
#                 "host": "host1",
#                 "port": "5555",
#                 "pgbouncer_host": "pgbouncer_host1",
#                 "pgbouncer_port": "5555",
#                 "dbname": "dbname1",
#             },
#         }
#         yield mock
#
#
# @pytest.fixture
# def mock_get_or_create_dify_blob_storage_values():
#     with patch(
#         "mlops_deployer.helm.apps.dify._get_or_create_dify_blob_storage_values",
#         new_callable=AsyncMock,
#     ) as mock:
#         # Set the return value to a mock DifyBlobStorageOutputs instance
#         mock.return_value = {
#             "externalS3": {
#                 "enabled": True,
#                 "endpoint": "endpoint_url",
#                 "accessKey": "AccessKey",
#                 "secretKey": "secret_access_key",
#                 "bucketName": "bucket_name",
#             }
#         }
#         yield mock
#
#
@pytest.fixture
def mock_get_preset_cpu():
    with (
        patch("apolo_app_types.helm.apps.common.get_preset") as mock,
        patch("apolo_app_types.helm.apps.llm.get_preset") as mock_llm,
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
                available_resource_pool_names=("default",),
            )

        mock.side_effect = return_preset
        mock_llm.side_effect = return_preset

        yield mock


@pytest.fixture
def mock_get_preset_gpu():
    with (
        patch("apolo_app_types.helm.apps.common.get_preset") as mock,
        patch("apolo_app_types.helm.apps.llm.get_preset") as mock_llm,
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
        yield mock
