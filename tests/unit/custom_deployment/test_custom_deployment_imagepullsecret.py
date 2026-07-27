import base64
import json
from unittest.mock import AsyncMock

import pytest
from apolo_app_types_fixtures.constants import APP_ID, APP_SECRETS_NAME

from apolo_app_types import ContainerImage
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import ApoloSecret, Preset
from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs
from apolo_app_types.protocols.dockerhub import DockerConfigModel
from apolo_app_types.protocols.github import GithubImageRegistryAuth


def _inputs(image: ContainerImage) -> CustomDeploymentInputs:
    return CustomDeploymentInputs(preset=Preset(name="cpu-small"), image=image)


async def _gen_values(setup_clients, image: ContainerImage) -> dict:
    _, helm_params = await app_type_to_vals(
        input_=_inputs(image),
        apolo_client=setup_clients,
        app_type=AppType.CustomDeployment,
        app_name="custom-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    return helm_params


@pytest.mark.asyncio
async def test_imagepullsecret_dockerconfig_passthrough(setup_clients):
    helm_params = await _gen_values(
        setup_clients,
        ContainerImage(
            repository="private.example.com/app",
            tag="v1",
            imagepullsecret=DockerConfigModel(filecontents="docker-config"),
        ),
    )
    assert helm_params["dockerconfigjson"] == "docker-config"


@pytest.mark.asyncio
async def test_imagepullsecret_github_rendering(setup_clients):
    setup_clients.secrets.get = AsyncMock(return_value=b"ghp_token\n")
    helm_params = await _gen_values(
        setup_clients,
        ContainerImage(
            repository="ghcr.io/org/app",
            tag="v1",
            imagepullsecret=GithubImageRegistryAuth(
                username="octocat",
                token=ApoloSecret(key="gh-pat"),
            ),
        ),
    )
    parsed = json.loads(base64.b64decode(helm_params["dockerconfigjson"]))
    expected_auth = base64.b64encode(b"octocat:ghp_token").decode()
    assert parsed == {"auths": {"ghcr.io": {"auth": expected_auth}}}
    setup_clients.secrets.get.assert_awaited_once_with(key="gh-pat")


@pytest.mark.asyncio
async def test_imagepullsecret_overrides_legacy_dockerconfigjson(setup_clients):
    helm_params = await _gen_values(
        setup_clients,
        ContainerImage(
            repository="private.example.com/app",
            tag="v1",
            dockerconfigjson=DockerConfigModel(filecontents="legacy-stale"),
            imagepullsecret=DockerConfigModel(filecontents="fresh"),
        ),
    )
    assert helm_params["dockerconfigjson"] == "fresh"


@pytest.mark.asyncio
async def test_legacy_dockerconfigjson_still_forwarded(setup_clients):
    helm_params = await _gen_values(
        setup_clients,
        ContainerImage(
            repository="private.example.com/app",
            tag="v1",
            dockerconfigjson=DockerConfigModel(filecontents="legacy-value"),
        ),
    )
    assert helm_params["dockerconfigjson"] == "legacy-value"


def test_container_image_schema_shape():
    schema = ContainerImage.model_json_schema()
    properties = schema["properties"]
    assert "imagepullsecret" in properties
    assert "dockerconfigjson" not in properties
    refs = {
        entry["$ref"]
        for entry in properties["imagepullsecret"]["anyOf"]
        if "$ref" in entry
    }
    assert refs == {
        "#/$defs/DockerConfigModel",
        "#/$defs/GithubImageRegistryAuth",
    }
