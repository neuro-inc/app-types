import logging

import apolo_sdk

from apolo_app_types.protocols.common.secrets_ import ApoloSecret


logger = logging.getLogger(__name__)

SECRET_KEY_TEMPLATE = "{key}-{app_instance_id}"


async def create_apolo_secret(
    app_instance_id: str, key: str, value: str
) -> ApoloSecret:
    secret_key = SECRET_KEY_TEMPLATE.format(key=key, app_instance_id=app_instance_id)
    try:
        async with apolo_sdk.get() as client:
            bytes_value = value.encode("utf-8")
            await client.secrets.add(key=secret_key, value=bytes_value)
    except Exception as e:
        logger.error("Failed to create Apolo Secret")
        raise (e)
    return ApoloSecret(key=secret_key)


async def delete_apolo_secret(
    app_instance_id: str, key: str, *, raise_not_found: bool = False
) -> None:
    secret_key = SECRET_KEY_TEMPLATE.format(key=key, app_instance_id=app_instance_id)
    try:
        async with apolo_sdk.get() as client:
            await client.secrets.rm(key=secret_key)
    except apolo_sdk.ResourceNotFound as e:
        logger.info("Secret not found")
        if raise_not_found:
            raise e
    except Exception as e:
        logger.error("Failed to delete Apolo Secret")
        raise (e)


async def get_apolo_secret(app_instance_id: str, key: str) -> str:
    secret_key = SECRET_KEY_TEMPLATE.format(key=key, app_instance_id=app_instance_id)
    try:
        async with apolo_sdk.get() as client:
            return (await client.secrets.get(key=secret_key)).decode()
    except Exception as e:
        logger.error("Failed to get Apolo Secret")
        raise (e)
