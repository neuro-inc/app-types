import pytest

from apolo_app_types import ContainerImage, CustomDeploymentInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.custom_deployment import CustomDeploymentModel


@pytest.mark.asyncio
async def test_custom_deployment_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=CustomDeploymentInputs(
            custom_deployment=CustomDeploymentModel(
                preset_name="basic-cpu",
                name_override="test-custom-deployment",
                image=ContainerImage(
                    repository="myrepo/custom-deployment", tag="v1.2.3"
                ),
            )
        ),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
    )
    assert helm_params["image"]["repository"] == "myrepo/custom-deployment"
    assert helm_params["image"]["tag"] == "v1.2.3"
