import json

import pytest

from apolo_app_types import (
    Container,
    ContainerImage,
    Env,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.common.health_check import (
    GRPCHealthCheckConfig,
    HealthCheck,
    HealthCheckProbesConfig,
    HTTPHealthCheckConfig,
    TCPHealthCheckConfig,
)
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
)
from apolo_app_types.protocols.custom_deployment import (
    ConfigMap,
    ConfigMapKeyValue,
    CustomDeploymentInputs,
    NetworkingConfig,
    StorageMounts,
)

from tests.unit.constants import APP_ID, APP_SECRETS_NAME


@pytest.mark.asyncio
async def test_custom_deployment_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            preset=Preset(name="cpu-small"),
            image=ContainerImage(repository="myrepo/custom-deployment", tag="v1.2.3"),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ports=[
                    Port(name="http", port=8080),
                ],
                ingress_http=IngressHttp(),
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"containerPort": 8080, "name": "http"}],
    }
    assert helm_params["ingress"]["enabled"] == True  # noqa: E712
    assert helm_params["ingress"]["className"] == "traefik"
    assert helm_params["preset_name"] == "cpu-small"


@pytest.mark.asyncio
async def test_custom_deployment_values_generation_with_storage_mounts(setup_clients):
    """
    Ensure that when storage_mounts are provided,
    we generate the correct podAnnotations and labels for Apolo storage injection.
    """
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            preset=Preset(name="cpu-small"),
            image=ContainerImage(
                repository="myrepo/custom-deployment",
                tag="v1.2.3",
            ),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ports=[
                    Port(name="http", port=8080),
                ],
                ingress_http=IngressHttp(),
            ),
            storage_mounts=StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path="storage://mycluster/myorg/myproj/data"
                        ),
                        mount_path=MountPath(path="/app/data"),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                    ApoloFilesMount(
                        storage_uri=ApoloFilesPath(
                            path="storage://mycluster/myorg/config"
                        ),
                        mount_path=MountPath(path="/config"),
                        mode=ApoloMountMode(mode="r"),
                    ),
                ]
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8080}],
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = json.loads(storage_json)
    assert len(parsed_storage) == 2

    assert parsed_storage[0]["storage_uri"] == "storage://mycluster/myorg/myproj/data"
    assert parsed_storage[0]["mount_path"] == "/app/data"
    assert parsed_storage[0]["mount_mode"] == "rw"

    assert parsed_storage[1]["storage_uri"] == "storage://mycluster/myorg/config"
    assert parsed_storage[1]["mount_path"] == "/config"
    assert parsed_storage[1]["mount_mode"] == "r"

    pod_labels = helm_params.get("podLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"


@pytest.mark.asyncio
async def test_custom_deployment_values_generation_with_multiport_exposure(
    setup_clients,
):
    """
    Ensure that when service is enabled, multiple ports supplied
    """
    custom_deploy_inputs = CustomDeploymentInputs(
        preset=Preset(name="cpu-small"),
        image=ContainerImage(
            repository="multiport",
            tag="latest",
        ),
        container=Container(
            command=["python", "app.py"],
            args=["--port", "8080"],
            env=[Env(name="ENV_VAR", value="value")],
        ),
        networking=NetworkingConfig(
            service_enabled=True,
            ports=[
                Port(name="http1", port=8000, path="/path_prefix1"),
                Port(name="http2", port=9000, path="/path_prefix2"),
            ],
            ingress_http=IngressHttp(),
        ),
    )
    helm_args, helm_params = await app_type_to_vals(
        input_=custom_deploy_inputs,
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_id=APP_ID,
        app_secrets_name=APP_SECRETS_NAME,
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "multiport",
        "tag": "latest",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"]["enabled"] == True  # noqa: E712
    assert helm_params["service"]["ports"] == [
        {"name": "http1", "containerPort": 8000},
        {"name": "http2", "containerPort": 9000},
    ]
    assert helm_params["ingress"]["enabled"] == True  # noqa: E712
    assert helm_params["ingress"]["className"] == "traefik"
    assert helm_params["ingress"]["hosts"][0]["paths"] == [
        {"path": "/path_prefix1", "pathType": "Prefix", "portName": "http1"},
        {"path": "/path_prefix2", "pathType": "Prefix", "portName": "http2"},
    ]


@pytest.mark.asyncio
async def test_custom_deployment_values_generation_path_port_not_supplied(
    setup_clients,
):
    """
    Ensure that when service is enabled, multiple ports supplied
    """
    custom_deploy_inputs = CustomDeploymentInputs(
        preset=Preset(name="cpu-small"),
        image=ContainerImage(
            repository="any",
            tag="latest",
        ),
        container=Container(
            command=["python", "app.py"],
            args=["--port", "8080"],
            env=[Env(name="ENV_VAR", value="value")],
        ),
        networking=NetworkingConfig(
            service_enabled=True,
            ports=[
                Port(name="http", port=8080),
            ],
            ingress_http=IngressHttp(),
        ),
    )
    helm_args, helm_params = await app_type_to_vals(
        input_=custom_deploy_inputs,
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "any",
        "tag": "latest",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"]["enabled"] == True  # noqa: E712
    assert helm_params["service"]["ports"] == [
        {"name": "http", "containerPort": 8080},
    ]
    assert helm_params["ingress"]["enabled"] == True  # noqa: E712
    assert helm_params["ingress"]["className"] == "traefik"
    assert helm_params["ingress"]["hosts"][0]["paths"] == [
        {"path": "/", "pathType": "Prefix", "portName": "http"},
    ]


@pytest.mark.asyncio
async def test_custom_deployment_values_generation_network_not_supplied(
    setup_clients,
):
    """
    Ensure that when service is enabled, multiple ports supplied
    """
    custom_deploy_inputs = CustomDeploymentInputs(
        preset=Preset(name="cpu-small"),
        image=ContainerImage(
            repository="any",
            tag="latest",
        ),
        container=Container(
            command=["python", "app.py"],
            args=["--port", "8080"],
            env=[Env(name="ENV_VAR", value="value")],
        ),
    )
    helm_args, helm_params = await app_type_to_vals(
        input_=custom_deploy_inputs,
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "any",
        "tag": "latest",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"]["enabled"] == True  # noqa: E712
    assert helm_params["service"]["ports"] == [
        {"name": "http", "containerPort": 80},
    ]
    assert helm_params["ingress"]["enabled"] == True  # noqa: E712
    assert helm_params["ingress"]["className"] == "traefik"
    assert helm_params["ingress"]["hosts"][0]["paths"] == [
        {"path": "/", "pathType": "Prefix", "portName": "http"},
    ]


@pytest.mark.asyncio
async def test_custom_deployment_values_generation_with_health_checks(
    setup_clients,
):
    """
    Ensure that when health checks are provided, they are properly
    configured in the helm values
    """
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            preset=Preset(name="cpu-small"),
            image=ContainerImage(
                repository="myrepo/custom-deployment",
                tag="v1.2.3",
            ),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ports=[
                    Port(name="http", port=8080),
                ],
                ingress_http=IngressHttp(),
            ),
            health_checks=HealthCheckProbesConfig(
                liveness=HealthCheck(
                    period=30,
                    initial_delay=10,
                    health_check_config=HTTPHealthCheckConfig(
                        path="/health",
                        port=8080,
                    ),
                ),
                startup=HealthCheck(
                    period=10,
                    initial_delay=5,
                    health_check_config=GRPCHealthCheckConfig(
                        service="service-name",
                        port=8080,
                    ),
                ),
                readiness=HealthCheck(
                    period=10,
                    initial_delay=5,
                    health_check_config=TCPHealthCheckConfig(
                        port=8080,
                    ),
                ),
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Base assertions
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8080}],
    }

    # Health check assertions
    assert "health_checks" in helm_params
    assert "livenessProbe" in helm_params["health_checks"]
    assert helm_params["health_checks"]["livenessProbe"] == {
        "httpGet": {"path": "/health", "port": 8080},
        "failureThreshold": 3,
        "timeoutSeconds": 1,
        "initialDelaySeconds": 10,
        "periodSeconds": 30,
    }
    assert "startupProbe" in helm_params["health_checks"]
    assert helm_params["health_checks"]["startupProbe"] == {
        "grpc": {"port": 8080, "service": "service-name"},
        "failureThreshold": 3,
        "timeoutSeconds": 1,
        "initialDelaySeconds": 5,
        "periodSeconds": 10,
    }
    assert "readinessProbe" in helm_params["health_checks"]
    assert helm_params["health_checks"]["readinessProbe"] == {
        "tcpSocket": {"port": 8080},
        "failureThreshold": 3,
        "timeoutSeconds": 1,
        "initialDelaySeconds": 5,
        "periodSeconds": 10,
    }


@pytest.mark.asyncio
async def test_custom_deployment_values_configmap_checks(
    setup_clients,
):
    """
    Ensure that when health checks are provided, they are properly
    configured in the helm values
    """
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            preset=Preset(name="cpu-small"),
            image=ContainerImage(
                repository="myrepo/custom-deployment",
                tag="v1.2.3",
            ),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ports=[
                    Port(name="http", port=8080),
                ],
                ingress_http=IngressHttp(),
            ),
            config_map=ConfigMap(
                mount_path=MountPath(path="/config"),
                data=[
                    ConfigMapKeyValue(key="config_key", value="config_value"),
                    ConfigMapKeyValue(key="config_key_2", value="config_value_2"),
                ],
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Base assertions
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8080}],
    }

    assert "configMap" in helm_params
    assert helm_params["configMap"] == {
        "enabled": True,
        "name": "app-configmap",
        "data": {"config_key": "config_value", "config_key_2": "config_value_2"},
    }
    assert {
        "name": "app-configmap",
        "configMap": {
            "name": "app-configmap",
        },
    } in helm_params["volumes"]
    assert {
        "name": "app-configmap",
        "mountPath": "/config",
    } in helm_params["volumeMounts"]


@pytest.mark.asyncio
async def test_custom_deployment_values_app_id(
    setup_clients,
):
    """
    Ensure that when health checks are provided, they are properly
    configured in the helm values
    """
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            preset=Preset(name="cpu-small"),
            image=ContainerImage(
                repository="myrepo/custom-deployment",
                tag="v1.2.3",
            ),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            networking=NetworkingConfig(
                service_enabled=True,
                ports=[
                    Port(name="http", port=8080),
                ],
                ingress_http=IngressHttp(),
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Base assertions
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
        "pullPolicy": "IfNotPresent",
    }
    assert helm_params["container"] == {
        "command": ["python", "app.py"],
        "args": ["--port", "8080"],
        "env": [{"name": "ENV_VAR", "value": "value"}],
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8080}],
    }

    assert helm_params["apolo_app_id"] == APP_ID
