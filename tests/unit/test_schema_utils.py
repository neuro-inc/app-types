from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.schema_utils import get_inline_schema


def test_get_inline_schema_simple():
    class SimpleInputs(AbstractAppFieldType):
        model_config = ConfigDict(
            json_schema_extra=SchemaExtraMetadata(
                title="Cool title", description="A simple input schema."
            ).as_json_schema_extra(),
        )
        name: str = Field(
            "default_name",
            json_schema_extra=SchemaExtraMetadata(
                title="Name", description="The name of the user."
            ).as_json_schema_extra(),
        )
        age: int = Field(30)

    schema = get_inline_schema(SimpleInputs)
    assert schema["title"] == "SimpleInputs"
    assert schema["type"] == "object"
    assert "properties" in schema
    assert schema["properties"]["name"]["default"] == "default_name"
    assert schema["properties"]["age"]["default"] == 30


def test_get_inline_schema_ref():
    class NestedInputs(AbstractAppFieldType):
        description: str = Field("A nested input")

    class RefInputs(AbstractAppFieldType):
        nested: NestedInputs
        count: int = Field(5)

    schema = get_inline_schema(RefInputs)
    assert schema["title"] == "RefInputs"
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "nested" in schema["properties"]
    assert schema["properties"]["nested"]["type"] == "object"
    assert (
        schema["properties"]["nested"]["properties"]["description"]["default"]
        == "A nested input"
    )
    assert schema["properties"]["count"]["default"] == 5
    assert "$defs" not in schema  # Ensure $defs is removed


def test_get_inline_schema_overwrite_defaults():
    class InnerInputs(AbstractAppFieldType):
        flag: bool = Field(default=False)
        value: float = Field(1.0)

    class OverwriteDefaults(AbstractAppFieldType):
        inner: InnerInputs = Field(InnerInputs(flag=True, value=2.5))
        count: int = Field(5)

    schema = get_inline_schema(OverwriteDefaults)
    assert schema["title"] == "OverwriteDefaults"
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "inner" in schema["properties"]
    assert schema["properties"]["inner"]["type"] == "object"
    assert schema["properties"]["inner"]["properties"]["flag"]["default"]
    assert schema["properties"]["inner"]["properties"]["value"]["default"] == 2.5
    assert schema["properties"]["count"]["default"] == 5
    assert "$defs" not in schema  # Ensure $defs is removed


def test_get_inline_schema_union():
    class OptionA(AbstractAppFieldType):
        option_a_field: str = Field("A")

    class OptionB(AbstractAppFieldType):
        option_b_field: int = Field(10)

    class UnionInputs(AbstractAppFieldType):
        option: OptionA | OptionB = Field(default=OptionA(option_a_field="CustomA"))

    schema = get_inline_schema(UnionInputs)
    assert schema["title"] == "UnionInputs"
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "option" in schema["properties"]
    assert "anyOf" in schema["properties"]["option"]
    found_a = False
    found_b = False
    for option_schema in schema["properties"]["option"]["anyOf"]:
        if option_schema.get("title") == "OptionA":
            found_a = True
            assert option_schema["properties"]["option_a_field"]["default"] == "CustomA"
        elif option_schema.get("title") == "OptionB":
            found_b = True
            assert option_schema["properties"]["option_b_field"]["default"] == 10
    assert found_a
    assert found_b
