from typing import Any, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


def find_instances_recursive(  # noqa: C901
    obj: Any, target_type: type[T], visited: set[Any] | None = None, _path: str = ""
) -> list[tuple[str, T]]:
    """
    Recursively search through a Pydantic object's attributes to find all instances
    of a specific type.

    Args:
        obj: The object to search through (typically a Pydantic model)
        target_type: The type to search for
        visited: Set to track visited objects and avoid circular references
        _path: Internal parameter to track the path to each found instance

    Returns:
        List of tuples containing (path, instance) for each match found
        Example: [('user.address', <Address object>),
                  ('user.billing_address', <Address object>)]
    """
    if visited is None:
        visited = set()

    # Avoid circular references
    obj_id = id(obj)
    if obj_id in visited:
        return []
    visited.add(obj_id)

    results: list[tuple[str, T]] = []

    # Check if the object itself is an instance of the target type
    if isinstance(obj, target_type):
        results.append((_path or "root", obj))

    # If it's a Pydantic model, iterate through its fields
    if isinstance(obj, BaseModel):
        for field_name, field_value in obj:
            field_path = f"{_path}.{field_name}" if _path else field_name
            results.extend(
                find_instances_recursive(field_value, target_type, visited, field_path)
            )

    # Handle lists and tuples
    elif isinstance(obj, list | tuple):
        for idx, item in enumerate(obj):
            item_path = f"{_path}[{idx}]" if _path else f"[{idx}]"
            results.extend(
                find_instances_recursive(item, target_type, visited, item_path)
            )

    # Handle dictionaries
    elif isinstance(obj, dict):
        for key, value in obj.items():
            dict_path = f"{_path}['{key}']" if _path else f"['{key}']"
            results.extend(
                find_instances_recursive(value, target_type, visited, dict_path)
            )

    # Handle sets
    elif isinstance(obj, set):
        for idx, item in enumerate(obj):
            set_path = f"{_path}{{item_{idx}}}" if _path else f"{{item_{idx}}}"
            results.extend(
                find_instances_recursive(item, target_type, visited, set_path)
            )

    return results


def find_instances_recursive_simple(obj: Any, target_type: type[T]) -> list[T]:
    """
    Simplified version that returns only the matching instances without paths.

    Args:
        obj: The object to search through (typically a Pydantic model)
        target_type: The type to search for

    Returns:
        List of all instances matching the target type
    """
    results_with_paths = find_instances_recursive(obj, target_type)
    return [instance for _, instance in results_with_paths]
