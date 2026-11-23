import pytest
from pydantic import ValidationError

from apolo_app_types import (
    TritonModelRepository,
    TritonModelRepositoryAppInputs,
    TritonModelRepositoryAppOutputs,
    TritonServerGRPCEndpoint,
    TritonServerHttpEndpoint,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.common.base import AppOutputs
from apolo_app_types.protocols.common.networking import GrpcAPI, RestAPI, ServiceAPI
from apolo_app_types.protocols.common.schema_extra import (
    X_CUSTOM_VALIDATORS_FIELD_NAME,
    X_META_TYPE_FIELD_NAME,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.storage import ApoloFilesPath


def _model_repository() -> TritonModelRepository:
    return TritonModelRepository(
        files_path=ApoloFilesPath(path="storage:triton/models")
    )


def test_triton_model_repository_construction():
    repository = _model_repository()
    assert repository.files_path.path == "storage:triton/models"


def test_triton_model_repository_rejects_non_storage_path():
    with pytest.raises(ValidationError, match="Storage path must have `storage:`"):
        TritonModelRepository(files_path=ApoloFilesPath(path="s3://bucket/models"))


def test_triton_model_repository_app_inputs_construction():
    inputs = TritonModelRepositoryAppInputs(model_repository=_model_repository())
    assert inputs.model_repository.files_path.path == "storage:triton/models"


def test_triton_model_repository_inputs_validate_as_outputs():
    inputs = TritonModelRepositoryAppInputs(model_repository=_model_repository())
    outputs = TritonModelRepositoryAppOutputs.model_validate(
        inputs.model_dump(exclude={"__type__"})
    )
    assert outputs.model_repository == inputs.model_repository


def test_app_type_triton_model_repository_is_appless():
    assert AppType.TritonModelRepository.is_appless() is True


def test_app_type_triton_is_not_appless():
    assert AppType.Triton.is_appless() is False


def test_app_type_triton_round_trip():
    assert AppType("triton") is AppType.Triton
    assert AppType("triton-model-repository") is AppType.TritonModelRepository


def test_triton_model_repository_schema_meta_type_is_integration():
    schema = TritonModelRepository.model_json_schema()
    assert schema[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INTEGRATION.value
    assert schema["x-type"] == "TritonModelRepository"


def test_triton_model_repository_schema_has_storage_path_validator():
    schema = TritonModelRepositoryAppInputs.model_json_schema()
    definition = schema["$defs"]["TritonModelRepository"]
    assert definition[X_CUSTOM_VALIDATORS_FIELD_NAME] == [
        {
            "storage_path_validator": {
                "exists": True,
                "is_dir": True,
                "same_project": True,
                "subfolder": True,
            }
        }
    ]
    assert definition["x-type"] == "TritonModelRepository"
    assert definition["required"] == ["files_path"]


def test_triton_model_repository_app_inputs_field_marked_inline():
    schema = TritonModelRepositoryAppInputs.model_json_schema()
    field = schema["properties"]["model_repository"]
    assert field["$ref"] == "#/$defs/TritonModelRepository"
    assert field[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INLINE.value


def test_triton_model_repository_app_outputs_field_is_integration():
    schema = TritonModelRepositoryAppOutputs.model_json_schema()
    assert schema["properties"]["model_repository"] == {
        "$ref": "#/$defs/TritonModelRepository"
    }
    definition = schema["$defs"]["TritonModelRepository"]
    assert definition[X_META_TYPE_FIELD_NAME] == SchemaMetaType.INTEGRATION.value


@pytest.mark.parametrize(
    ("endpoint_type", "parent_type", "api_type"),
    [
        (TritonServerHttpEndpoint, RestAPI, "rest"),
        (TritonServerGRPCEndpoint, GrpcAPI, "grpc"),
    ],
)
def test_triton_endpoint_keeps_own_x_type(endpoint_type, parent_type, api_type):
    endpoint = endpoint_type(host="triton-abc.default", port=8000)
    assert endpoint.api_type == api_type
    assert endpoint_type.model_json_schema()["x-type"] == endpoint_type.__name__
    assert parent_type.model_json_schema()["x-type"] == parent_type.__name__


@pytest.mark.parametrize(
    ("endpoint_type", "definition_name"),
    [
        (TritonServerHttpEndpoint, "ServiceAPI_TritonServerHttpEndpoint_"),
        (TritonServerGRPCEndpoint, "ServiceAPI_TritonServerGRPCEndpoint_"),
    ],
)
def test_triton_endpoint_service_api_definition_name(endpoint_type, definition_name):
    class Outputs(AppOutputs):
        endpoint: ServiceAPI[endpoint_type] | None = None

    schema = Outputs.model_json_schema()
    assert schema["properties"]["endpoint"]["anyOf"][0] == {
        "$ref": f"#/$defs/{definition_name}"
    }
    definition = schema["$defs"][definition_name]
    assert definition["properties"]["external_url"]["anyOf"][0] == {
        "$ref": f"#/$defs/{endpoint_type.__name__}"
    }
