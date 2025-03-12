import pytest

from apolo_app_types import (
    Container,
    ContainerImage,
    CustomDeploymentInputs,
    Env,
    Service,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.custom_deployment import CustomDeploymentModel


@pytest.mark.asyncio
async def test_custom_deployment_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            custom_deployment=CustomDeploymentModel(
                preset=Preset(name="cpu-small"),
                name_override="custom-deployment",
                image=ContainerImage(
                    repository="myrepo/custom-deployment", tag="v1.2.3"
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
                    enabled=True,
                    clusterName="default",
                ),
            )
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
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
