from typing import get_type_hints

from pydantic import BaseModel


def validate_complex_type_prop(cls: type[BaseModel]) -> None:
    for field_name, field_type in get_type_hints(cls).items():
        if not (isinstance(field_type, type) and issubclass(field_type, BaseModel)):
            raise TypeError(
                f"Field '{field_name}' in {cls.__name__} must be a subclass of Pydantic BaseModel, "
                f"but got {field_type}"
            )
