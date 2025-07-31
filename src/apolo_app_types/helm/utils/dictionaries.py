from functools import reduce
from typing import Any

from apolo_app_types.helm.utils.deep_merging import deep_merge


def get_value_from_nested_key(dictionary: dict[str, Any], key: str) -> Any:
    if "." not in key:
        return {key: dictionary.get(key)}

    cur_key, next_keys = key.split(".", maxsplit=1)
    if cur_key in dictionary:
        return {cur_key: get_value_from_nested_key(dictionary[cur_key], next_keys)}
    return None


def get_nested_values(dictionary: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """
    Retrieve nested keys from a dictionary.

    Args:
        dictionary (dict): The dictionary to search.
        keys (list[str]): List of keys to retrieve.

    Returns:
        dict: A dictionary containing the requested keys and their values.
    """
    dicts = []
    for key in keys:
        dicts.append(get_value_from_nested_key(dictionary, key))

    return reduce(deep_merge, dicts, {})
