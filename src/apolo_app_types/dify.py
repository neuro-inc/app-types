from apolo_app_types.common import AppInputs, AppOutputs


class ExternalPostgres:
    platform_app_name: str
    username: str | None
    db_name: str | None


class ExternalPGVector:
    platform_app_name: str
    username: str | None
    db_name: str | None


class DifyInputs(AppInputs):
    class Api:
        replicas: int | None
        preset_name: str

    class Worker:
        replicas: int | None
        preset_name: str

    class Proxy:
        preset_name: str

    class Web:
        replicas: int | None
        preset_name: str

    class Redis:
        class Master:
            preset_name: str

        master: Master

    api: Api
    worker: Worker
    proxy: Proxy
    web: Web
    redis: Redis
    externalPostgres: ExternalPostgres
    externalPGVector: ExternalPGVector


class DifyOutputs(AppOutputs):
    internal_web_app_url: str
    internal_api_url: str
    external_api_url: str | None
    init_password: str
