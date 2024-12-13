from apolo_app_types.common import AppOutputs


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
