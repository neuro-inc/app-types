import typing as t

from pydantic import BaseModel, SecretStr


def pydantic_to_serialized_dict(  # noqa: C901
    obj: t.Any,
    parent_key: str = "",
    sep: str = ".",
) -> dict[str, t.Any]:
    """Converts a Pydantic model to a serialized dictionary with flattened keys."""
    items: list[t.Any] = []

    if isinstance(obj, BaseModel):
        obj = obj.model_dump()

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (BaseModel | dict)):
                items.extend(pydantic_to_serialized_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, (BaseModel | dict)):
                        items.extend(
                            pydantic_to_serialized_dict(
                                item, f"{new_key}[{i}]", sep=sep
                            ).items()
                        )
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_key = f"{parent_key}[{i}]"
            if isinstance(item, (BaseModel | dict)):
                items.extend(
                    pydantic_to_serialized_dict(item, new_key, sep=sep).items()
                )
            else:
                items.append((new_key, item))

    else:
        items.append((parent_key, obj))

    return dict(items)


def replace_secrets(d: t.Any) -> t.Any:
    """Convert a dictionary to replace SecretStr values with plain strings."""

    def unpack_secret(value: t.Any) -> t.Any:
        if isinstance(value, SecretStr):
            return value.get_secret_value()  # Unpack SecretStr to a plain string
        if isinstance(value, dict):
            return {k: unpack_secret(v) for k, v in value.items()}
        if isinstance(value, list):
            return [unpack_secret(v) for v in value]
        return value

    return unpack_secret(d)
