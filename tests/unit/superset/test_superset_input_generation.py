import pytest

from apolo_app_types import CrunchyPostgresUserCredentials
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.superset import (
    SupersetInputs,
    SupersetPostgresConfig,
    SupersetUserConfig,
    WebConfig,
    WorkerConfig,
)

from tests.unit.constants import APP_ID, APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_superset_basic_values_generation(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=SupersetInputs(
            worker_config=WorkerConfig(preset=Preset(name="cpu-large")),
            web_config=WebConfig(preset=Preset(name="cpu-large")),
            ingress_http=IngressHttp(),
            postgres_config=SupersetPostgresConfig(preset=Preset(name="cpu-large")),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Superset,
        app_name="superset",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    assert helm_params["supersetNode"] == {
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "platform.neuromation.io/nodepool",
                                    "operator": "In",
                                    "values": ["cpu_pool"],
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "apolo_app_id": APP_ID,
        "podLabels": {
            "platform.apolo.us/component": "app",
            "platform.apolo.us/preset": "cpu-large",
        },
        "preset_name": "cpu-large",
        "resources": {
            "limits": {"cpu": "1000.0m", "memory": "0M"},
            "requests": {"cpu": "1000.0m", "memory": "0M"},
        },
        "tolerations": [
            {
                "effect": "NoSchedule",
                "key": "platform.neuromation.io/job",
                "operator": "Exists",
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/not-ready",
                "operator": "Exists",
                "tolerationSeconds": 300,
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/unreachable",
                "operator": "Exists",
                "tolerationSeconds": 300,
            },
        ],
    }
    assert helm_params["postgres"] == {
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "platform.neuromation.io/nodepool",
                                    "operator": "In",
                                    "values": ["cpu_pool"],
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "apolo_app_id": APP_ID,
        "podLabels": {
            "platform.apolo.us/component": "app",
            "platform.apolo.us/preset": "cpu-large",
        },
        "preset_name": "cpu-large",
        "resources": {
            "limits": {"cpu": "1000.0m", "memory": "0M"},
            "requests": {"cpu": "1000.0m", "memory": "0M"},
        },
        "tolerations": [
            {
                "effect": "NoSchedule",
                "key": "platform.neuromation.io/job",
                "operator": "Exists",
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/not-ready",
                "operator": "Exists",
                "tolerationSeconds": 300,
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/unreachable",
                "operator": "Exists",
                "tolerationSeconds": 300,
            },
        ],
    }
    assert helm_params["supersetWorker"] == {
        "apolo_app_id": APP_ID,
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "platform.neuromation.io/nodepool",
                                    "operator": "In",
                                    "values": ["cpu_pool"],
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "podLabels": {
            "platform.apolo.us/component": "worker",
            "platform.apolo.us/preset": "cpu-large",
        },
        "preset_name": "cpu-large",
        "resources": {
            "limits": {"cpu": "1000.0m", "memory": "0M"},
            "requests": {"cpu": "1000.0m", "memory": "0M"},
        },
        "tolerations": [
            {
                "effect": "NoSchedule",
                "key": "platform.neuromation.io/job",
                "operator": "Exists",
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/not-ready",
                "operator": "Exists",
                "tolerationSeconds": 300,
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/unreachable",
                "operator": "Exists",
                "tolerationSeconds": 300,
            },
        ],
    }
    assert helm_params["init"] == {
        "adminUser": {
            "email": "admin@superset.com",
            "firstname": "Superset",
            "lastname": "Admin",
            "password": "admin",
            "username": "admin",
        }
    }
    assert helm_params["extraSecretEnv"]["SUPERSET_SECRET_KEY"]


@pytest.mark.asyncio
async def test_superset_values_generation_with_postgres_integration(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=SupersetInputs(
            worker_config=WorkerConfig(preset=Preset(name="cpu-large")),
            web_config=WebConfig(preset=Preset(name="cpu-large")),
            ingress_http=IngressHttp(),
            postgres_config=CrunchyPostgresUserCredentials(
                user="pgvector_user",
                password="pgvector_password",
                host="pgvector_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=4321,
                dbname="db_name",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Superset,
        app_name="superset",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["postgres"]["enabled"] == False
    assert helm_params["supersetNode"]["connections"] == {
        "db_host": "pgbouncer_host",
        "db_name": "db_name",
        "db_pass": "pgvector_password",
        "db_port": 4321,
        "db_user": "pgvector_user",
    }


@pytest.mark.asyncio
async def test_superset_values_generation_with_custom_admin_user(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=SupersetInputs(
            worker_config=WorkerConfig(preset=Preset(name="cpu-large")),
            web_config=WebConfig(preset=Preset(name="cpu-large")),
            ingress_http=IngressHttp(),
            admin_user=SupersetUserConfig(
                username="some_other_admin_user",
                firstname="Superset",
                lastname="Admin",
                password="MyCrazyPass",
                email="admin@mail.ua",
            ),
            postgres_config=SupersetPostgresConfig(preset=Preset(name="cpu-large")),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Superset,
        app_name="superset",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["init"]["adminUser"] == {
        "email": "admin@mail.ua",
        "firstname": "Superset",
        "lastname": "Admin",
        "password": "MyCrazyPass",
        "username": "some_other_admin_user",
    }
