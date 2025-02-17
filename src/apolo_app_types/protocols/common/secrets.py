from pydantic import BaseModel


class Secret(BaseModel):
    name: str
    key: str


class SecretKeyRef(BaseModel):
    secretKeyRef: Secret  # noqa: N815


class K8sSecret(BaseModel):
    valueFrom: SecretKeyRef  # noqa: N815


StrOrSecret = str | K8sSecret
OptionalStrOrSecret = StrOrSecret | None
