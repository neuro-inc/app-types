import base64
from contextlib import AsyncExitStack
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from apolo_sdk import AppsConfig


def encode_b64(value: str) -> str:
    """Helper function to encode a string in Base64."""
    return base64.b64encode(value.encode()).decode()


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
            if preset_name == "gpu-large":
                return Preset(
                    credits_per_hour=Decimal("1.0"),
                    cpu=1.0,
                    memory=100,
                    nvidia_gpu=4,
                    available_resource_pool_names=("gpu_pool",),
                )
            if preset_name == "gpu-xlarge":
                return Preset(
                    credits_per_hour=Decimal("1.0"),
                    cpu=1.0,
                    memory=100,
                    nvidia_gpu=8,
                    available_resource_pool_names=("gpu_pool",),
                )
            # Fallback (e.g., "gpu-large" = 1 GPU)
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


@pytest.fixture
def mock_kubernetes_client():
    with (
        patch("kubernetes.config.load_config") as mock_load_config,
        patch("kubernetes.config.load_incluster_config") as mock_load_incluster_config,
        patch("kubernetes.client.CoreV1Api") as mock_core_v1_api,
        patch("kubernetes.client.NetworkingV1Api") as mock_networking_v1_api,
        patch(
            "apolo_app_types.clients.kube.get_current_namespace"
        ) as mock_get_curr_namespace,
    ):
        # Mock CoreV1Api instance for services
        mock_v1_instance = MagicMock()
        mock_core_v1_api.return_value = mock_v1_instance

        # Mock NetworkingV1Api instance for ingresses
        mock_networking_instance = MagicMock()
        mock_networking_v1_api.return_value = mock_networking_instance
        namespace = "default-namespace"
        mock_get_curr_namespace.return_value = namespace
        # Define the fake response for list_namespaced_service

        # Define the fake response for list_namespaced_ingress
        fake_ingresses = {
            "items": [
                {
                    "metadata": {"name": "ingress-1"},
                    "spec": {"rules": [{"host": "example.com"}]},
                }
            ]
        }

        def get_services_by_label(namespace, label_selector):
            if label_selector == "application=weaviate":
                return {
                    "items": [
                        {
                            "metadata": {"name": "weaviate", "namespace": namespace},
                            "spec": {"ports": [{"port": 80}]},
                        },
                        {
                            "metadata": {
                                "name": "weaviate-grpc",
                                "namespace": namespace,
                            },
                            "spec": {"ports": [{"port": 443}]},
                        },
                    ]
                }
            if label_selector == "application=llm-inference":
                return {
                    "items": [
                        {
                            "metadata": {
                                "name": "llm-inference",
                                "namespace": namespace,
                            },
                            "spec": {"ports": [{"port": 80}]},
                        }
                    ]
                }
            return {
                "items": [
                    {
                        "metadata": {
                            "name": "app",
                            "namespace": "default-namespace",
                        },
                        "spec": {"ports": [{"port": 80}]},
                    },
                ]
            }

        def list_namespace_ingress(namespace, label_selector):
            return fake_ingresses

        mock_v1_instance.list_namespaced_service.side_effect = get_services_by_label
        mock_networking_instance.list_namespaced_ingress.side_effect = (
            list_namespace_ingress
        )

        def list_namespace_secret(namespace: str, label_selector: str):
            return {
                "items": [
                    {
                        "metadata": {
                            "name": "llm-inference",
                            "namespace": namespace,
                        },
                        "data": {
                            "user": encode_b64("admin"),
                            "password": encode_b64("supersecret"),
                            "host": encode_b64("db.example.com"),
                            "port": encode_b64("5432"),
                            "pgbouncer-host": encode_b64("pgbouncer.example.com"),
                            "pgbouncer-port": encode_b64("6432"),
                            "dbname": encode_b64("mydatabase"),
                            "jdbc-uri": encode_b64(
                                "jdbc:postgresql://db.example.com:5432/mydatabase"
                            ),
                            "pgbouncer-jdbc-uri": encode_b64(
                                "jdbc:postgresql://pgbouncer.example.com:6432/mydatabase"
                            ),
                            "pgbouncer-uri": encode_b64(
                                "postgres://pgbouncer.example.com:6432/mydatabase"
                            ),
                            "uri": encode_b64(
                                "postgres://db.example.com:5432/mydatabase"
                            ),
                        },
                    }
                ]
            }

        mock_v1_instance.list_namespaced_secret.side_effect = list_namespace_secret

        yield {
            "mock_load_config": mock_load_config,
            "mock_load_incluster_config": mock_load_incluster_config,
            "mock_core_v1_api": mock_core_v1_api,
            "mock_networking_v1_api": mock_networking_v1_api,
            "mock_v1_instance": mock_v1_instance,
            "mock_networking_instance": mock_networking_instance,
            "fake_ingresses": fake_ingresses,
        }
