import base64
from contextlib import AsyncExitStack
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import apolo_sdk
import pytest
from apolo_sdk import AppsConfig, Preset
from apolo_sdk._server_cfg import NvidiaGPUPreset
from neuro_config_client import NodePool
from yarl import URL

from .constants import (
    DEFAULT_CLUSTER_NAME,
    DEFAULT_ORG_NAME,
    DEFAULT_PROJECT_NAME,
    TEST_PRESETS,
)


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
            fake_node_pools = [
                NodePool(
                    name="cpu-pool",
                    cpu=2.0,
                    available_cpu=2.0,
                    memory=8192,
                    available_memory=8192,
                    disk_size=100000,
                    available_disk_size=100000,
                ),
                NodePool(
                    name="gpu-small",
                    cpu=2.0,
                    available_cpu=2.0,
                    memory=8192,
                    available_memory=8192,
                    disk_size=100000,
                    available_disk_size=100000,
                ),
                NodePool(
                    name="misc-pool",
                    cpu=2.0,
                    available_cpu=2.0,
                    memory=8192,
                    available_memory=8192,
                    disk_size=100000,
                    available_disk_size=100000,
                ),
            ]
            mock_apolo_client._clusters._client.list_node_pools = AsyncMock(
                return_value=fake_node_pools
            )
            mock_get.return_value.__aenter__.return_value = mock_apolo_client
            apolo_client = await stack.enter_async_context(mock_get())
            yield apolo_client
            await stack.aclose()


def encode_b64(value: str) -> str:
    """Helper function to encode a string in Base64."""
    return base64.b64encode(value.encode()).decode()


@pytest.fixture
def presets_available(request):
    return getattr(request, "param", TEST_PRESETS)


@pytest.fixture
def mock_get_preset_cpu():
    with (
        patch("apolo_app_types.helm.apps.common.get_preset") as mock,
        patch("apolo_app_types.helm.apps.llm.get_preset") as mock_llm,
        patch("apolo_app_types.helm.apps.stable_diffusion.get_preset") as mock_sd,
        patch("apolo_app_types.helm.apps.text_embeddings.get_preset") as mock_tei,
    ):

        def return_preset(_, preset_name):
            if preset_name in TEST_PRESETS:
                return TEST_PRESETS[preset_name]

            return Preset(
                credits_per_hour=Decimal("1.0"),
                cpu=1.0,
                memory=100,
                available_resource_pool_names=("cpu_pool",),
            )

        mock.side_effect = return_preset
        mock_llm.side_effect = return_preset
        mock_sd.side_effect = return_preset
        mock_tei.side_effect = return_preset

        yield mock


@pytest.fixture
def mock_get_preset_gpu():
    with (
        patch("apolo_app_types.helm.apps.common.get_preset") as mock,
        patch("apolo_app_types.helm.apps.llm.get_preset") as mock_llm,
        patch("apolo_app_types.helm.apps.stable_diffusion.get_preset") as mock_sd,
        patch("apolo_app_types.helm.apps.text_embeddings.get_preset") as mock_tei,
    ):
        from apolo_sdk import Preset

        def return_preset(_, preset_name):
            if preset_name in TEST_PRESETS:
                return TEST_PRESETS[preset_name]

            return Preset(
                credits_per_hour=Decimal("1.0"),
                cpu=1.0,
                memory=100,
                nvidia_gpu=NvidiaGPUPreset(count=1, memory=16),
                available_resource_pool_names=("gpu_pool",),
            )

        mock.side_effect = return_preset
        mock_llm.side_effect = return_preset
        mock_sd.side_effect = return_preset
        mock_tei.side_effect = return_preset
        yield mock


@pytest.fixture
def mock_kubernetes_client():
    with (
        patch("kubernetes.config.load_config") as mock_load_config,
        patch("kubernetes.config.load_incluster_config") as mock_load_incluster_config,
        patch("kubernetes.client.CoreV1Api") as mock_core_v1_api,
        patch("kubernetes.client.NetworkingV1Api") as mock_networking_v1_api,
        patch("kubernetes.client.CustomObjectsApi") as mock_custom_objects_api,
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
            if (
                label_selector
                == "application=weaviate,app.kubernetes.io/instance=test-app-instance-id"  # noqa: E501
            ):
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
            if (
                label_selector
                == "application=llm-inference,app.kubernetes.io/instance=test-app-instance-id"  # noqa: E501
            ):
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
            if (
                label_selector
                == "app.kubernetes.io/name=lightrag,app.kubernetes.io/instance=test-app-instance-id"  # noqa: E501
            ):
                return {
                    "items": [
                        {
                            "metadata": {
                                "name": "lightrag",
                                "namespace": namespace,
                            },
                            "spec": {"ports": [{"port": 9621}]},
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
        user_params = {
            "password": encode_b64("supersecret"),
            "host": encode_b64("db.example.com"),
            "port": encode_b64("5432"),
            "pgbouncer-host": encode_b64("pgbouncer.example.com"),
            "pgbouncer-port": encode_b64("6432"),
            "dbname": encode_b64("mydatabase"),
            "jdbc-uri": encode_b64("jdbc:postgresql://db.example.com:5432/mydatabase"),
            "pgbouncer-jdbc-uri": encode_b64(
                "jdbc:postgresql://pgbouncer.example.com:6432/mydatabase"
            ),
            "pgbouncer-uri": encode_b64(
                "postgres://pgbouncer.example.com:6432/mydatabase"
            ),
            "uri": encode_b64("postgres://db.example.com:5432/mydatabase"),
        }
        mock_secret = MagicMock()
        mock_secret.metadata.name = "llm-inference"
        mock_secret.metadata.namespace = "default"
        mock_secret.data = {
            "user": encode_b64("admin"),
            **user_params,
        }
        mock_postgres_secret = MagicMock()
        mock_postgres_secret.metadata.name = "llm-inference"
        mock_postgres_secret.metadata.namespace = "default"
        mock_postgres_secret.data = {
            "user": encode_b64("postgres"),
            **user_params,
        }

        # Set .items to a list containing the mocked secret
        mock_v1_instance.list_namespaced_secret.return_value.items = [
            mock_secret,
            mock_postgres_secret,
        ]

        def mock_list_namespaced_custom_object(
            group, version, namespace, plural, **kwargs
        ):
            if (
                group == "postgres-operator.crunchydata.com"
                and version == "v1beta1"
                and plural == "postgresclusters"
            ):
                return {
                    "items": [
                        {
                            "spec": {
                                "users": [
                                    {
                                        "name": "admin",
                                        "databases": ["mydatabase", "otherdatabase"],
                                    },
                                    {
                                        "name": "postgres",
                                        "databases": ["postgres"],
                                    },
                                ]
                            }
                        }
                    ]
                }
            raise Exception("Unknown custom object")  # noqa: EM101

        mock_custom_objects_instance = MagicMock()
        mock_custom_objects_api.return_value = mock_custom_objects_instance
        mock_custom_objects_instance.list_namespaced_custom_object.side_effect = (
            mock_list_namespaced_custom_object
        )

        yield {
            "mock_load_config": mock_load_config,
            "mock_load_incluster_config": mock_load_incluster_config,
            "mock_core_v1_api": mock_core_v1_api,
            "mock_networking_v1_api": mock_networking_v1_api,
            "mock_v1_instance": mock_v1_instance,
            "mock_networking_instance": mock_networking_instance,
            "mock_custom_objects": mock_custom_objects_instance,
            "fake_ingresses": fake_ingresses,
        }


@pytest.fixture
def app_instance_id():
    """Fixture to provide a mock app instance ID."""
    return "test-app-instance-id"
