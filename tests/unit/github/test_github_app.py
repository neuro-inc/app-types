import jsonschema
import pytest

from apolo_app_types import (
    GithubAppInputs,
    GithubAppOutputs,
    GithubAuth,
    GithubImageRegistryAuth,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.common.schema_extra import (
    X_META_TYPE_FIELD_NAME,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret


def test_github_auth_defaults_api_url():
    auth = GithubAuth(username="octocat", token=ApoloSecret(key="gh-token"))
    assert auth.api_url == "https://api.github.com"
    assert auth.username == "octocat"
    assert isinstance(auth.token, ApoloSecret)
    assert auth.token.key == "gh-token"


def test_github_auth_custom_api_url():
    auth = GithubAuth(
        username="octocat",
        token=ApoloSecret(key="gh-token"),
        api_url="https://github.example.com/api/v3",
    )
    assert auth.api_url == "https://github.example.com/api/v3"


def test_github_image_registry_auth_defaults_registry_url():
    registry_auth = GithubImageRegistryAuth(
        username="octocat", token=ApoloSecret(key="gh-token")
    )
    assert registry_auth.registry_url == "ghcr.io"
    assert isinstance(registry_auth.token, ApoloSecret)


def test_github_image_registry_auth_custom_registry_url():
    registry_auth = GithubImageRegistryAuth(
        registry_url="containers.github.example.com",
        username="octocat",
        token=ApoloSecret(key="gh-token"),
    )
    assert registry_auth.registry_url == "containers.github.example.com"


def test_github_app_inputs_construction():
    inputs = GithubAppInputs(
        auth=GithubAuth(username="octocat", token=ApoloSecret(key="gh-token")),
        image_registry_auth=GithubImageRegistryAuth(
            username="octocat", token=ApoloSecret(key="gh-token")
        ),
    )
    assert inputs.auth.username == "octocat"
    assert inputs.image_registry_auth.registry_url == "ghcr.io"


# Appless install stores input_params verbatim as outputs after validating
# them against the OUTPUT schema, so inputs must satisfy the outputs schema.


@pytest.fixture
def github_app_inputs() -> GithubAppInputs:
    return GithubAppInputs(
        auth=GithubAuth(
            username="octocat",
            token=ApoloSecret(key="gh-token"),
        ),
        image_registry_auth=GithubImageRegistryAuth(
            username="octocat",
            token=ApoloSecret(key="gh-registry-token"),
        ),
    )


def test_github_app_inputs_validate_against_outputs_schema(github_app_inputs):
    dumped = github_app_inputs.model_dump(mode="json")
    output_schema = GithubAppOutputs.model_json_schema()
    jsonschema.validate(instance=dumped, schema=output_schema)


def test_github_app_inputs_load_as_outputs(github_app_inputs):
    dumped = github_app_inputs.model_dump(mode="json")
    outputs = GithubAppOutputs.model_validate(dumped)
    assert outputs.auth.username == "octocat"
    assert outputs.auth.api_url == "https://api.github.com"
    assert outputs.image_registry_auth.registry_url == "ghcr.io"
    assert outputs.image_registry_auth.username == "octocat"


def test_app_type_github_is_appless():
    assert AppType.Github.is_appless() is True


def test_app_type_github_round_trip():
    assert AppType("github") == AppType.Github
    assert AppType("github") is AppType.Github


def test_github_auth_schema_meta_type_is_integration():
    schema = GithubAuth.model_json_schema()
    assert schema[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INTEGRATION.value


def test_github_image_registry_auth_schema_meta_type_is_integration():
    schema = GithubImageRegistryAuth.model_json_schema()
    assert schema[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INTEGRATION.value


def test_github_app_inputs_nested_fields_marked_inline():
    schema = GithubAppInputs.model_json_schema()
    auth_extra = schema["properties"]["auth"]
    registry_auth_extra = schema["properties"]["image_registry_auth"]
    assert auth_extra[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INLINE.value
    assert registry_auth_extra[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INLINE.value
