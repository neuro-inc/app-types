import enum
import importlib
import json
import pkgutil

import pytest
from pydantic import BaseModel, ValidationError

import apolo_app_types
from apolo_app_types.protocols.common import (
    OpenAICompatAPI,
    OpenAICompatCapability,
    OpenAICompatModel,
    ServiceAPI,
)
from apolo_app_types.protocols.common.openai_compat import get_api_base_url


def gateway_api() -> OpenAICompatAPI:
    return OpenAICompatAPI(
        host="bifrost.namespace",
        port=8080,
        models=[
            OpenAICompatModel(
                name="vllm/meta-llama/Llama-3.1-8B-Instruct",
                capabilities=[
                    OpenAICompatCapability.CHAT,
                    OpenAICompatCapability.COMPLETIONS,
                    OpenAICompatCapability.RESPONSES,
                ],
            ),
            OpenAICompatModel(
                name="vllm/BAAI/bge-small-en-v1.5",
                capabilities=[OpenAICompatCapability.EMBEDDINGS],
            ),
            OpenAICompatModel(
                name="openai/text-embedding-3-small",
                capabilities=[OpenAICompatCapability.EMBEDDINGS],
            ),
        ],
    )


SERIALIZED_SERVICE = {
    "internal_url": {
        "host": "bifrost.namespace",
        "port": 8080,
        "protocol": "http",
        "timeout": 30.0,
        "base_path": "/",
        "api_type": "rest",
        "api_base_path": "/v1",
        "models": [
            {
                "name": "vllm/meta-llama/Llama-3.1-8B-Instruct",
                "capabilities": ["chat", "completions", "responses"],
                "__type__": "OpenAICompatModel",
            },
            {
                "name": "vllm/BAAI/bge-small-en-v1.5",
                "capabilities": ["embeddings"],
                "__type__": "OpenAICompatModel",
            },
            {
                "name": "openai/text-embedding-3-small",
                "capabilities": ["embeddings"],
                "__type__": "OpenAICompatModel",
            },
        ],
        "__type__": "OpenAICompatAPI",
    },
    "external_url": None,
    "__type__": "ServiceAPI[OpenAICompatAPI]",
}


def test_schema_marks_an_integration() -> None:
    schema = ServiceAPI[OpenAICompatAPI].model_json_schema()
    api = schema["$defs"]["OpenAICompatAPI"]

    assert api["x-type"] == "OpenAICompatAPI"
    assert api["x-meta-type"] == "integration"
    assert schema["$defs"]["OpenAICompatModel"]["x-type"] == "OpenAICompatModel"


def test_schema_does_not_close_the_capabilities() -> None:
    schema = ServiceAPI[OpenAICompatAPI].model_json_schema()

    assert schema["$defs"]["OpenAICompatModel"]["properties"]["capabilities"][
        "items"
    ] == {"type": "string"}
    assert "OpenAICompatCapability" not in schema["$defs"]


def test_serialized_form() -> None:
    service = ServiceAPI[OpenAICompatAPI](internal_url=gateway_api())

    assert json.loads(service.model_dump_json()) == SERIALIZED_SERVICE
    assert service.model_dump(mode="json") == SERIALIZED_SERVICE


def test_serialized_form_validates_back() -> None:
    service = ServiceAPI[OpenAICompatAPI].model_validate(SERIALIZED_SERVICE)

    assert service == ServiceAPI[OpenAICompatAPI](internal_url=gateway_api())
    assert service.internal_url is not None
    assert (
        json.loads(service.internal_url.model_dump_json())
        == (SERIALIZED_SERVICE["internal_url"])
    )


def test_defaults() -> None:
    api = OpenAICompatAPI(host="gateway")

    assert api.models == []
    assert get_api_base_url(api) == "http://gateway:80/v1"


def test_unknown_capability_is_kept() -> None:
    data = json.loads(gateway_api().model_dump_json())
    data["models"].append(
        {
            "name": "vllm/BAAI/bge-reranker-base",
            "capabilities": ["rerank"],
            "__type__": "OpenAICompatModel",
        }
    )

    api = OpenAICompatAPI.model_validate(data)

    assert api.get_model_names("rerank") == ["vllm/BAAI/bge-reranker-base"]
    assert api.get_model_names(OpenAICompatCapability.CHAT) == [
        "vllm/meta-llama/Llama-3.1-8B-Instruct"
    ]
    assert json.loads(api.model_dump_json()) == data


def test_model_name_is_required() -> None:
    with pytest.raises(ValidationError):
        OpenAICompatModel(name="", capabilities=[OpenAICompatCapability.CHAT])


def test_model_names_by_capability() -> None:
    api = gateway_api()

    assert api.get_model_names(OpenAICompatCapability.CHAT) == [
        "vllm/meta-llama/Llama-3.1-8B-Instruct"
    ]
    assert api.get_model_names("embeddings") == [
        "vllm/BAAI/bge-small-en-v1.5",
        "openai/text-embedding-3-small",
    ]
    assert api.get_model_names("rerank") == []
    assert get_api_base_url(api) == "http://bifrost.namespace:8080/v1"


def test_exported_from_the_package() -> None:
    assert apolo_app_types.OpenAICompatAPI is OpenAICompatAPI
    assert apolo_app_types.OpenAICompatModel is OpenAICompatModel
    assert apolo_app_types.OpenAICompatCapability is OpenAICompatCapability


def _type_names() -> set[str]:
    for module in pkgutil.walk_packages(
        apolo_app_types.__path__, f"{apolo_app_types.__name__}."
    ):
        importlib.import_module(module.name)
    names = set()
    classes: list[type] = [BaseModel, enum.Enum]
    while classes:
        cls = classes.pop()
        classes.extend(cls.__subclasses__())
        if cls.__module__.startswith(apolo_app_types.__name__):
            names.add(cls.__name__)
    return names


@pytest.mark.parametrize(
    "name",
    [
        "OpenAICompatAPI",
        "OpenAICompatModel",
        "OpenAICompatCapability",
    ],
)
def test_type_name_does_not_overlap_other_types(name: str) -> None:
    others = _type_names() - {name, f"ServiceAPI[{name}]"}

    assert {
        "OpenAICompatChatAPI",
        "OpenAICompatEmbeddingsAPI",
        "OpenAICompatibleAPI",
        "OpenAICompatibleChatAPI",
        "OpenAICompatibleEmbeddingsRestAPI",
    } <= others
    assert [other for other in others if name.lower() in other.lower()] == []
    assert [other for other in others if other.lower() in name.lower()] == []
