import asyncio
import base64
import logging
import typing as t

from tenacity import retry, stop_after_attempt, wait_exponential

from apolo_app_types import (
    CrunchyPostgresUserCredentials,
)
from apolo_app_types.clients.kube import get_crd_objects, get_secret
from apolo_app_types.outputs.utils.apolo_secrets import create_apolo_secret
from apolo_app_types.protocols.common import ApoloSecret
from apolo_app_types.protocols.postgres import (
    PostgresAdminUser,
    PostgresOutputs,
    PostgresURI,
    PostgresUsers,
)


logger = logging.getLogger()

MAX_SLEEP_SEC = 10
POSTGRES_ADMIN_USERNAME = "postgres"


APP_SECRET_KEYS = {
    "LAUNCHPAD": "launchpad-admin-pswd",
    "KEYCLOAK": "keycloak-admin-pswd",
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(exp_base=2, multiplier=2),
)
async def create_apolo_secret_with_retry(
    app_instance_id: str, key: str, value: str
) -> ApoloSecret:
    """
    Attempt to create an Apolo secret with retry logic using exponential backoff.
    Retries up to 5 times with delays: 2s, 4s, 8s, 16s, 32s.
    Returns the secret reference on success.
    Raises exception if all retries fail.
    """
    logger.info('Creating secret "%s-%s"', key, app_instance_id)
    result = await create_apolo_secret(
        app_instance_id=app_instance_id, key=key, value=value
    )
    logger.info('Successfully created secret "%s-%s"', key, app_instance_id)
    return result


def get_postgres_cluster_users() -> dict[str, t.Any]:
    pg_clusters = get_crd_objects(
        api_group="postgres-operator.crunchydata.com",
        api_version="v1beta1",
        crd_plural_name="postgresclusters",
    )
    assert len(pg_clusters["items"]) == 1, "Expected exactly one Postgres cluster"
    pg_cluster = pg_clusters["items"][0]
    users = pg_cluster["spec"].get("users", [])
    return {user["name"]: user for user in users}


async def postgres_creds_from_kube_secret_data(
    secret_data: dict[str, str],
    app_instance_id: str,
    database_override: str | None = None,
) -> CrunchyPostgresUserCredentials:
    """
    Create Postgres user credentials from Kubernetes secret data.

    Args:
        secret_data: Base64-encoded secret data from Kubernetes
        app_instance_id: Application instance ID for secret naming
        database_override: If provided, use this database name instead of the one
                          in secret_data and replace database names in all URIs
    """
    T = t.TypeVar("T", str, str | None)

    def _b64decode(s: T) -> T:
        if not isinstance(s, str):
            return s
        return base64.b64decode(s).decode()

    user = _b64decode(secret_data["user"])
    password_value = _b64decode(secret_data["password"])
    host = _b64decode(secret_data["host"])
    port = _b64decode(secret_data["port"])
    pgbouncer_host = _b64decode(secret_data["pgbouncer-host"])
    pgbouncer_port = _b64decode(secret_data["pgbouncer-port"])
    original_dbname = _b64decode(secret_data.get("dbname"))

    # Use override database or the original
    dbname = database_override if database_override is not None else original_dbname
    # Include database in secret key if it's an override
    db_suffix = f"-{dbname}" if database_override else ""

    postgres_conn_string = f"postgresql://{user}:{password_value}@{pgbouncer_host}:{pgbouncer_port}/{dbname}"

    # Create Apolo secrets for all sensitive fields
    password = await create_apolo_secret_with_retry(
        app_instance_id=app_instance_id,
        key=f"postgres-{user}-password",
        value=password_value,
    )

    # Helper to replace database in URI if override is provided
    def maybe_replace_db(uri_value: str | None) -> str | None:
        if uri_value and database_override and original_dbname:
            return uri_value.replace(f"/{original_dbname}", f"/{database_override}")
        return uri_value

    # Create secrets for optional URI fields if they exist
    jdbc_uri = None
    jdbc_uri_value = maybe_replace_db(_b64decode(secret_data.get("jdbc-uri")))
    if jdbc_uri_value:
        jdbc_uri = await create_apolo_secret_with_retry(
            app_instance_id=app_instance_id,
            key=f"postgres-{user}{db_suffix}-jdbc-uri",
            value=jdbc_uri_value,
        )

    pgbouncer_jdbc_uri = None
    pgbouncer_jdbc_uri_value = maybe_replace_db(
        _b64decode(secret_data.get("pgbouncer-jdbc-uri"))
    )
    if pgbouncer_jdbc_uri_value:
        pgbouncer_jdbc_uri = await create_apolo_secret_with_retry(
            app_instance_id=app_instance_id,
            key=f"postgres-{user}{db_suffix}-pgbouncer-jdbc-uri",
            value=pgbouncer_jdbc_uri_value,
        )

    pgbouncer_uri = None
    pgbouncer_uri_value = maybe_replace_db(_b64decode(secret_data.get("pgbouncer-uri")))
    if pgbouncer_uri_value:
        pgbouncer_uri = await create_apolo_secret_with_retry(
            app_instance_id=app_instance_id,
            key=f"postgres-{user}{db_suffix}-pgbouncer-uri",
            value=pgbouncer_uri_value,
        )

    uri = None
    uri_value = maybe_replace_db(_b64decode(secret_data.get("uri")))
    if uri_value:
        uri = await create_apolo_secret_with_retry(
            app_instance_id=app_instance_id,
            key=f"postgres-{user}{db_suffix}-uri",
            value=uri_value,
        )

    # Create secret for the postgres connection string
    postgres_uri_secret = await create_apolo_secret_with_retry(
        app_instance_id=app_instance_id,
        key=f"postgres-{user}{db_suffix}-connection-uri",
        value=postgres_conn_string,
    )

    return CrunchyPostgresUserCredentials(
        user=user,
        password=password,
        host=host,
        port=int(port),
        pgbouncer_host=pgbouncer_host,
        pgbouncer_port=int(pgbouncer_port),
        dbname=dbname,
        jdbc_uri=jdbc_uri,
        pgbouncer_jdbc_uri=pgbouncer_jdbc_uri,
        pgbouncer_uri=pgbouncer_uri,
        uri=uri,
        postgres_uri=PostgresURI(uri=postgres_uri_secret),
    )


async def get_postgres_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    for trial in range(1, MAX_SLEEP_SEC):
        logger.info("Trying to get postgres outputs")  # noqa: T201
        secrets = await get_secret(
            label="postgres-operator.crunchydata.com/role=pguser"
        )
        if secrets:
            logger.info("Secrets found")  # noqa: T201
            break
        logger.info(  # noqa: T201
            "Failed to get postgres outputs, retrying in %s seconds", trial
        )
        await asyncio.sleep(trial)
    else:
        msg = "Failed to get postgres outputs"
        raise Exception(msg)

    requested_users = get_postgres_cluster_users()
    users = []
    admin_user = None

    for item in secrets.items:
        user = await postgres_creds_from_kube_secret_data(item.data, app_instance_id)
        if user.user == POSTGRES_ADMIN_USERNAME:
            admin_user = user
            continue
        users.append(user)
        # currently, postgres operator does not create all combinations of
        # user <> database accesses, we need to expand this
        requested_dbs = requested_users.get(user.user, {}).get("databases", [])
        for db in requested_dbs:
            if user.dbname == db:
                continue
            # Create new credentials for this database with proper secrets
            db_user = await postgres_creds_from_kube_secret_data(
                item.data, app_instance_id, database_override=db
            )
            users.append(db_user)
    if admin_user:
        admin = PostgresAdminUser(
            **{**admin_user.model_dump(exclude={"dbname"}), "user_type": "admin"}
        )
    else:
        admin = None
    return PostgresOutputs(
        postgres_users=PostgresUsers(
            users=users,
            postgres_admin_user=admin,
        ),
    ).model_dump()
