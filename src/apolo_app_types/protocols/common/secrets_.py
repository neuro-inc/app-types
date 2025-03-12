from typing import Literal

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
