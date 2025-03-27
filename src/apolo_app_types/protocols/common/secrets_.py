from typing import Any, Literal

from pydantic import ConfigDict

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)

class ApoloSecret(BaseModel):
    name: Literal["apps-secrets"] = "apps-secrets"
    key: str  # noqa: N815


StrOrSecret = str | ApoloSecret
OptionalStrOrSecret = StrOrSecret | None


def serialize_optional_secret(value: OptionalStrOrSecret) -> dict[str, Any] | str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, ApoloSecret):
        return {
            "valueFrom": {
                "secretKeyRef": {
                    "name": value.name,
                    "key": value.key,
                }
            }
        }
    err_msg = f"Unsupported type for secret val: {type(value)}"
    raise ValueError(err_msg)
