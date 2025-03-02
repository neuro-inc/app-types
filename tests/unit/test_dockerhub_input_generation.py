import pytest

from apolo_app_types import DockerHubInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.dockerhub import DockerHubModel

from tests.unit.constants import DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_values_dockerhub_generation_(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=DockerHubInputs(
            dockerhub=DockerHubModel(username="test", password="test")
        ),
        apolo_client=apolo_client,
        app_type=AppType.DockerHub,
        app_name="dockerhub",
        namespace=DEFAULT_NAMESPACE,
    )

    assert helm_params["job"]["args"]["org"] == apolo_client.config.org_name
    assert helm_params["job"]["args"]["namespace"] == DEFAULT_NAMESPACE
    assert helm_params["job"]["args"]["project"] == apolo_client.config.project_name
    assert helm_params["job"]["args"]["user"] == apolo_client.username
    assert helm_params["job"]["args"]["registry_name"] == "DockerHub"
    assert (
        helm_params["job"]["args"]["registry_provider_host"]
        == "https://index.docker.io/v1/"
    )
    assert helm_params["job"]["args"]["registry_api_url"] == "https://hub.docker.com"
    assert helm_params["job"]["args"]["registry_user"] == "test"
    assert helm_params["job"]["args"]["registry_secret"] == "test"
