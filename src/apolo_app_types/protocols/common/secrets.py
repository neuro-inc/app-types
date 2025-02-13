from pydantic import BaseModel


class SecretKeyRef(BaseModel):
    name: str
    key: str


class K8sSecret(BaseModel):
    valueFrom: SecretKeyRef  # noqa: N815


StrOrSecret = str | K8sSecret
OptionalStrOrSecret = StrOrSecret | None
