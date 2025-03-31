import pytest

from apolo_app_types import (
    Container,
    ContainerImage,
    Env,
    Service,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
)
from apolo_app_types.protocols.custom_deployment import (
    CustomDeploymentInputs,
    DeploymentName,
    StorageMounts,
)

from tests.unit.constants import APP_SECRETS_NAME


@pytest.mark.asyncio
async def test_custom_deployment_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            preset=Preset(name="cpu-small"),
            name_override=DeploymentName(name="custom-deployment"),
            image=ContainerImage(repository="myrepo/custom-deployment", tag="v1.2.3"),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            service=Service(
                enabled=True,
                port=8080,
            ),
            ingress=Ingress(
                enabled=True,
                clusterName="default",
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
        "port": 8080,
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
            name_override=DeploymentName(name="custom-deployment"),
            image=ContainerImage(
                repository="myrepo/custom-deployment",
                tag="v1.2.3",
            ),
            container=Container(
                command=["python", "app.py"],
                args=["--port", "8080"],
                env=[Env(name="ENV_VAR", value="value")],
            ),
            service=Service(
                enabled=True,
                port=8080,
            ),
            ingress=Ingress(
                enabled=False,
                clusterName="default",
            ),
            storage_mounts=StorageMounts(
                mounts=[
                    ApoloFilesMount(
                        storage_path=ApoloFilesPath(
                            path="storage://mycluster/myorg/myproj/data"
                        ),
                        mount_path=MountPath(path="/app/data"),
                        mode=ApoloMountMode(mode="rw"),
                    ),
                    ApoloFilesMount(
                        storage_path=ApoloFilesPath(
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
        "port": 8080,
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    from json import loads

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = loads(storage_json)
    assert len(parsed_storage) == 2

    assert parsed_storage[0]["storage_path"] == "storage://mycluster/myorg/myproj/data"
    assert parsed_storage[0]["mount_path"] == "/app/data"
    assert parsed_storage[0]["mount_mode"] == "rw"

    assert parsed_storage[1]["storage_path"] == "storage://mycluster/myorg/config"
    assert parsed_storage[1]["mount_path"] == "/config"
    assert parsed_storage[1]["mount_mode"] == "r"

    pod_labels = helm_params.get("podExtraLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"
