import copy
import typing as t
from functools import reduce


def deep_merge(dict1: dict[str, t.Any], dict2: dict[str, t.Any]) -> dict[str, t.Any]:
    """Recursively merges two dictionaries."""
    merged = copy.deepcopy(dict1)
    for key, value in dict2.items():
        if key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = deep_merge(merged[key], value)
            elif isinstance(merged[key], list) and isinstance(value, list):
                merged[key].extend(value)
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged


def merge_list_of_dicts(dict_list: list[dict[str, t.Any]]) -> dict[str, t.Any]:
    """Merges a list of dictionaries using deep_merge."""
    return reduce(deep_merge, dict_list, {})
