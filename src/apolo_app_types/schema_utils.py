from typing import Any

import jsonref
from pydantic import BaseModel


def _is_top_level_schema(schema: dict[str, Any]) -> bool:
    return (
        isinstance(schema, dict)
        and "properties" in schema
        and "title" in schema
        and "type" in schema
    )


def _replace_downstream_defaults(  # noqa: C901
    schema: dict[str, Any], defaults: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Recursively replace default values in a JSON schema with those from
      a defaults dictionary.

    Args:
        schema (dict): The original JSON schema.
        defaults (dict): A dictionary containing default values to
            replace in the schema.

    Returns:
        dict: The modified JSON schema with updated default values.
    """
    if not isinstance(schema, dict):
        return schema

    if defaults is None:
        defaults = {}
        if schema.get("type") == "object" and "default" in schema:
            defaults = schema["default"]

    if _is_top_level_schema(schema):
        value_dict = schema["properties"]
        for prop, prop_schema in value_dict.items():
            new_defaults = None
            if prop in defaults:
                new_defaults = defaults[prop]
                del defaults[prop]
                if prop_schema.get("type") not in ["array", "object"]:
                    prop_schema["default"] = new_defaults
            _replace_downstream_defaults(prop_schema, new_defaults)
    else:
        for _, value in schema.items():
            if isinstance(value, dict):
                _replace_downstream_defaults(value, defaults)
            elif isinstance(value, list):
                for item in value:
                    new_default = defaults
                    if (
                        "default" in schema
                        and isinstance(schema["default"], dict)
                        and schema["default"].get("__type__", "")
                        == item.get("title", "")
                    ):
                        new_default = schema["default"]
                    _replace_downstream_defaults(item, new_default)

    if (
        isinstance(schema.get("default"), dict)
        and schema.get("type") == "object"
        and schema["default"] == {}
    ):
        del schema["default"]
    return schema


def get_inline_schema(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    new_schema = jsonref.replace_refs(schema, merge_props=True, proxies=False)
    new_schema = _replace_downstream_defaults(new_schema)
    if "$defs" in new_schema:
        del new_schema["$defs"]
    return new_schema
