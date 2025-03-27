from typing import Any, Literal

from pydantic import ConfigDict

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class Secret(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Secret",
            description="Apolo Secret Configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    name: Literal["apps-secrets"] = "apps-secrets"
    key: str


class SecretKeyRef(AbstractAppFieldType):
    secretKeyRef: Secret  # noqa: N815


class K8sSecret(AbstractAppFieldType):
    valueFrom: SecretKeyRef  # noqa: N815


StrOrSecret = str | K8sSecret
OptionalStrOrSecret = StrOrSecret | None


def serialize_optional_secret(value: OptionalStrOrSecret) -> dict[str, Any] | str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, K8sSecret):
        return value.model_dump()
    err_msg = f"Unsupported type for secret val: {type(value)}"
    raise ValueError(err_msg)
