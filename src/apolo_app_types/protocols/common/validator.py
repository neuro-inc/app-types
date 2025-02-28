from types import UnionType
from typing import get_args, get_origin, get_type_hints

from pydantic import BaseModel


def validate_complex_type_prop(cls: type[BaseModel]) -> None:
    for field_name, field_type in get_type_hints(cls).items():
        origin = get_origin(field_type)
        args = get_args(field_type)

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            continue

        if origin is UnionType and all(
            isinstance(arg, type) and (issubclass(arg, BaseModel) or arg is type(None))
            for arg in args
        ):
            continue

        err_msg = (
            f"Field '{field_name}' in {cls.__name__} "
            f"must be a subclass of Pydantic BaseModel, "
            f"but got {field_type}"
        )
        raise TypeError(err_msg)
