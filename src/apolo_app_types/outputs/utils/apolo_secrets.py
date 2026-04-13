from __future__ import annotations

import asyncio
import logging

import apolo_sdk
from apolo_app_types.protocols.common.secrets_ import ApoloSecret


logger = logging.getLogger(__name__)

SECRET_KEY_TEMPLATE = "{key}-{app_instance_id}"

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BASE_DELAY_SECONDS = 2


async def create_apolo_secret(
    app_instance_id: str, key: str, value: str
) -> ApoloSecret:
    secret_key = SECRET_KEY_TEMPLATE.format(key=key, app_instance_id=app_instance_id)
    try:
        async with apolo_sdk.get() as client:
            bytes_value = value.encode("utf-8")
            await client.secrets.add(key=secret_key, value=bytes_value)
    except Exception:
        logger.exception("Failed to create Apolo Secret")
        raise
    return ApoloSecret(key=secret_key)


async def create_apolo_secret_with_retry(
    app_instance_id: str,
    key: str,
    value: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay_seconds: float = DEFAULT_BASE_DELAY_SECONDS,
) -> ApoloSecret:
    attempt = 0
    while True:
        try:
            logger.info(
                'Creating secret "%s-%s" (attempt %d)',
                key,
                app_instance_id,
                attempt + 1,
            )
            result = await create_apolo_secret(
                app_instance_id=app_instance_id, key=key, value=value
            )
            logger.info('Successfully created secret "%s-%s"', key, app_instance_id)
            return result
        except Exception as exc:
            attempt += 1
            if attempt >= max_attempts:
                logger.exception(
                    'All %d attempts failed to create secret "%s-%s"',
                    max_attempts,
                    key,
                    app_instance_id,
                )
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                'Attempt %d failed to create secret "%s-%s": %s. '
                "Retrying in %s seconds",
                attempt,
                key,
                app_instance_id,
                exc,
                delay,
            )
            await asyncio.sleep(delay)


async def delete_apolo_secret(
    app_instance_id: str, key: str, *, raise_not_found: bool = False
) -> None:
    secret_key = SECRET_KEY_TEMPLATE.format(key=key, app_instance_id=app_instance_id)
    try:
        async with apolo_sdk.get() as client:
            await client.secrets.rm(key=secret_key)
    except apolo_sdk.ResourceNotFound:
        logger.info("Secret not found")
        if raise_not_found:
            raise
    except Exception:
        logger.exception("Failed to delete Apolo Secret")
        raise


async def get_apolo_secret(app_instance_id: str, key: str) -> str:
    secret_key = SECRET_KEY_TEMPLATE.format(key=key, app_instance_id=app_instance_id)
    try:
        async with apolo_sdk.get() as client:
            return (await client.secrets.get(key=secret_key)).decode()
    except Exception:
        logger.exception("Failed to get Apolo Secret")
        raise
