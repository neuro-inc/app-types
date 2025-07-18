from apolo_app_types.protocols.postgres import CrunchyPostgresUserCredentials


def get_postgres_database_url(credentials: CrunchyPostgresUserCredentials) -> str:
    if credentials.postgres_uri and credentials.postgres_uri.uri:
        return credentials.postgres_uri.uri

    return f"postgresql://{credentials.user}:{credentials.password}@{credentials.pgbouncer_host}:{credentials.pgbouncer_port}/{credentials.dbname}"  # noqa: E501
