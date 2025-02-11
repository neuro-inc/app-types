from pydantic import BaseModel


class SecretKeyRef(BaseModel):
    name: str
    key: str


class K8sSecret(BaseModel):
    valueFrom: SecretKeyRef
