import base64
import itertools
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from apolo_sdk import Preset
from apolo_sdk._server_cfg import NvidiaGPUPreset

from tests.unit.constants import (
    CUSTOM_AUTH_MIDDLEWARE,
    CUSTOM_RATE_LIMITING_MIDDLEWARE,
    DATABASE_POSTGRES,
    DATABASE_SQLITE,
    DEFAULT_AUTH_MIDDLEWARE,
    TEST_PRESETS,
)


pytest_plugins = ["apolo_app_types_fixtures"]


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


# OpenWebUI Test Case Generation


@dataclass
class OpenWebUITestCase:
    """Configuration for a single OpenWebUI test case."""

    auth_enabled: bool
    middleware_name: str | None
    database_type: str

    @property
    def expected_middleware(self) -> list[str]:
        """Compute expected middleware based on configuration."""
        middleware = []
        if self.auth_enabled:
            middleware.append(DEFAULT_AUTH_MIDDLEWARE)
        if self.middleware_name:
            middleware.append(self.middleware_name)
        return middleware

    @property
    def expected_db_url(self) -> str | None:
        """Compute expected database URL for assertions."""
        if self.database_type == DATABASE_SQLITE:
            return None
        if self.database_type == DATABASE_POSTGRES:
            return "postgresql://pgvector_user:pgvector_password@pgbouncer_host:4321/db_name"
        return None

    @property
    def test_id(self) -> str:
        """Generate a descriptive test ID."""
        auth_part = "auth_enabled" if self.auth_enabled else "auth_disabled"

        if self.middleware_name:
            # Extract the descriptive part from middleware name
            if "custom-auth-middleware" in self.middleware_name:
                middleware_part = "with_auth_middleware"
            elif "rate-limiting-middleware" in self.middleware_name:
                middleware_part = "with_rate_limiting_middleware"
            else:
                middleware_part = "with_middleware"
        else:
            middleware_part = "no_middleware"

        return f"{auth_part}_{middleware_part}_{self.database_type}"


def _generate_openwebui_test_cases() -> list[OpenWebUITestCase]:
    """Generate all combinations of OpenWebUI test configurations."""
    auth_options = [True, False]
    middleware_options = [None, CUSTOM_AUTH_MIDDLEWARE, CUSTOM_RATE_LIMITING_MIDDLEWARE]
    database_options = [DATABASE_SQLITE, DATABASE_POSTGRES]

    test_cases = []

    for auth, middleware, db_type in itertools.product(
        auth_options, middleware_options, database_options
    ):
        test_cases.append(
            OpenWebUITestCase(
                auth_enabled=auth,
                middleware_name=middleware,
                database_type=db_type,
            )
        )

    return test_cases


@pytest.fixture(params=_generate_openwebui_test_cases(), ids=lambda tc: tc.test_id)
def openwebui_test_case(request):
    """Provide individual OpenWebUI test case configurations."""
    return request.param
