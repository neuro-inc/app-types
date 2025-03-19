from typing import Any, Literal

from pydantic import BaseModel


class Secret(BaseModel):
    name: Literal["apps-secrets"] = "apps-secrets"
    key: str


class SecretKeyRef(BaseModel):
    secretKeyRef: Secret  # noqa: N815


class K8sSecret(BaseModel):
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
