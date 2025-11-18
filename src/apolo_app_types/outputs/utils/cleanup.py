import logging

import apolo_sdk
from tenacity import retry, stop_after_attempt, wait_exponential

from apolo_app_types.outputs.utils.type_search import find_instances_recursive_simple
from apolo_app_types.protocols.common import ApoloSecret, AppOutputs


logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(exp_base=2, multiplier=2),
)
async def delete_secret_with_retry(secret_key: str, client: apolo_sdk.Client) -> None:
    """
    Attempt to delete a secret with retry logic using exponential backoff.
    Retries up to 5 times with delays: 2s, 4s, 8s, 16s, 32s.
    Logs warnings on failure but does not raise exceptions on final failure.
    """
    logger.info('Deleting secret "%s"', secret_key)
    await client.secrets.rm(key=secret_key)
    logger.info('Successfully deleted secret "%s"', secret_key)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(exp_base=2, multiplier=2),
)
async def get_app_outputs(
    app_id: str, output_class: type[AppOutputs], client: apolo_sdk.Client
) -> AppOutputs | None:
    output = await client.apps.get_output(app_id=app_id)
    if output:
        return output_class.model_validate(output)
    return None


async def cleanup_secrets(
    app_id: str, output_class: type[AppOutputs], client: apolo_sdk.Client
) -> None:
    app_outputs = await get_app_outputs(
        app_id=app_id, output_class=output_class, client=client
    )
    secrets = find_instances_recursive_simple(obj=app_outputs, target_type=ApoloSecret)

    for secret in secrets:
        try:
            await delete_secret_with_retry(secret_key=secret.key, client=client)
        except Exception as e:
            logger.error(
                'Failed to delete secret "%s" after all retries: %s', secret.key, e
            )
