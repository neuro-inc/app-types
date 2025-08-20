from typing import Any

from pydantic import ConfigDict

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class ApoloSecret(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Secret",
            description="Apolo Secret Configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    key: str


OptionalSecret = ApoloSecret | None


def serialize_optional_secret(
    value: OptionalSecret, secret_name: str
) -> dict[str, Any] | str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, ApoloSecret):
        return {
            "valueFrom": {
                "secretKeyRef": {
                    "name": secret_name,
                    "key": value.key,
                }
            }
        }
    err_msg = f"Unsupported type for secret val: {type(value)}"
    raise ValueError(err_msg)
