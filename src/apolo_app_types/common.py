from pydantic import BaseModel, ConfigDict


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AppOutputs(BaseModel):
    external_web_app_url: str | None = None


class IngressGrpc(BaseModel):
    enabled: bool


class Ingress(BaseModel):
    enabled: str
    clusterName: str  # noqa: N815
    grpc: IngressGrpc | None = None


class HuggingFaceModel(AppInputs):
    modelHFName: str  # noqa: N815
    modelFiles: str | None  # noqa: N815


class RedisMaster(BaseModel):
    preset_name: str


class Redis(BaseModel):
    master: RedisMaster


class Postgres:
    platform_app_name: str
    username: str | None
    db_name: str | None


class PostgresWithPGVector(BaseModel):
    platform_app_name: str
    username: str | None
    db_name: str | None
