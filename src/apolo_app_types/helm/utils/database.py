from apolo_app_types.protocols.common import ApoloSecret
from apolo_app_types.protocols.postgres import CrunchyPostgresUserCredentials


def get_postgres_database_url(
    credentials: CrunchyPostgresUserCredentials,
) -> ApoloSecret:
    """
    Get the Postgres database URL from credentials.

    Prioritizes pgbouncer URLs over direct postgres connections.
    Returns an ApoloSecret reference.
    """
    # First try pgbouncer_uri (preferred for connection pooling)
    if credentials.pgbouncer_uri:
        return credentials.pgbouncer_uri

    # Fall back to direct postgres_uri
    if credentials.postgres_uri:
        return credentials.postgres_uri

    # If no URI is available, we cannot build a connection string
    # because password is an ApoloSecret and cannot be interpolated into a string
    msg = (
        "Cannot build database URL: either pgbouncer_uri or postgres_uri "
        "is required when using ApoloSecret credentials"
    )
    raise ValueError(msg)
