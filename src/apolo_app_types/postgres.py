from apolo_app_types.common import AppInputs, AppOutputs


class CrunchyPostgresInputs(AppInputs):
    preset_name: str
    postgres_version: str
    instance_replicas: int
    pg_bouncer_preset_name: str
    pg_bouncer_replicas: int


class CrunchyPostgresUserCredentials(AppOutputs):
    user: str
    password: str
    host: str
    port: str
    pgbouncer_host: str
    pgbouncer_port: str
    dbname: str | None = None
    jdbc_uri: str | None = None
    pgbouncer_jdbc_uri: str | None = None
    pgbouncer_uri: str | None = None
    uri: str | None = None


class CrunchyPostgresOutputs(AppOutputs):
    users: list[CrunchyPostgresUserCredentials]
