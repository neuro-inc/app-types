import asyncio
import base64
import logging
import typing as t

from apolo_app_types import (
    CrunchyPostgresUserCredentials,
)
from apolo_app_types.clients.kube import get_secret
from apolo_app_types.protocols.postgres import PostgresOutputsV2


logger = logging.getLogger()

MAX_SLEEP_SEC = 10


def postgres_creds_from_kube_secret_data(
    secret_data: dict[str, str],
) -> CrunchyPostgresUserCredentials:
    T = t.TypeVar("T", str, str | None)

    def _b64decode(s: T) -> T:
        if not isinstance(s, str):
            return s
        return base64.b64decode(s).decode()

    return CrunchyPostgresUserCredentials(
        user=_b64decode(secret_data["user"]),
        password=_b64decode(secret_data["password"]),
        host=_b64decode(secret_data["host"]),
        port=_b64decode(secret_data["port"]),
        pgbouncer_host=_b64decode(secret_data["pgbouncer-host"]),
        pgbouncer_port=_b64decode(secret_data["pgbouncer-port"]),
        dbname=_b64decode(secret_data.get("dbname")),
        jdbc_uri=_b64decode(secret_data.get("jdbc-uri")),
        pgbouncer_jdbc_uri=_b64decode(secret_data.get("pgbouncer-jdbc-uri")),
        pgbouncer_uri=_b64decode(secret_data.get("pgbouncer-uri")),
        uri=_b64decode(secret_data.get("uri")),
    )


async def get_postgres_outputs(
    _: dict[str, t.Any],
) -> dict[str, t.Any]:
    for trial in range(1, MAX_SLEEP_SEC):
        logger.info("Trying to get postgres outputs")  # noqa: T201
        secrets = await get_secret(
            label="postgres-operator.crunchydata.com/role=pguser"
        )
        if secrets:
            break
        logger.info(  # noqa: T201
            "Failed to get postgres outputs, retrying in %s seconds", trial
        )
        await asyncio.sleep(trial)
    else:
        msg = "Failed to get postgres outputs"
        raise Exception(msg)
    users = []

    for item in secrets["items"]:
        users.append(postgres_creds_from_kube_secret_data(item["data"]))
    return PostgresOutputsV2(users=users).model_dump()
