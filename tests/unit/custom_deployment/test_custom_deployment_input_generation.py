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
from apolo_app_types.protocols.common.k8s import Port
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
)
from apolo_app_types.protocols.custom_deployment import (
    CustomDeploymentInputs,
    NetworkingConfig,
    StorageMounts,
)

from tests.unit.constants import APP_SECRETS_NAME


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
    )
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
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
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "myrepo/custom-deployment",
        "tag": "v1.2.3",
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
        app_secrets_name=APP_SECRETS_NAME,
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "multiport",
        "tag": "latest",
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
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "any",
        "tag": "latest",
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
    )

    # The base checks from the existing test
    assert helm_params["image"] == {
        "repository": "any",
        "tag": "latest",
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
