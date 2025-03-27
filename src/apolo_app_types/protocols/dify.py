from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputsDeployer,
    AppOutputsDeployer,
    Postgres,
    Redis,
)


class DifyApi(AbstractAppFieldType):
    replicas: int | None
    preset_name: str
    title: str


class DifyWorker(AbstractAppFieldType):
    replicas: int | None
    preset_name: str


class DifyProxy(AbstractAppFieldType):
    preset_name: str


class DifyWeb(AbstractAppFieldType):
    replicas: int | None
    preset_name: str


class DifyInputs(AppInputsDeployer):
    api: DifyApi
    worker: DifyWorker
    proxy: DifyProxy
    web: DifyWeb
    redis: Redis
    externalPostgres: Postgres  # noqa: N815
    externalPGVector: Postgres  # noqa: N815


class DifyOutputs(AppOutputsDeployer):
    internal_web_app_url: str
    internal_api_url: str
    external_api_url: str | None
    init_password: str
