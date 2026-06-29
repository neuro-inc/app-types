"""Authentication parameter validation utilities."""

import logging
import os

import apolo_sdk
import click


logger = logging.getLogger(__name__)


async def validate_auth_params(
    apolo_api_token: str | None,
    apolo_api_url: str | None,
    apolo_passed_config: str | None,
) -> None:
    """Validate authentication parameters.

    This function validates that either token+URL or passed_config is provided.
    If both are null, it attempts to get a client using default credentials.

    Args:
        apolo_api_token: The Apolo API token
        apolo_api_url: The Apolo API URL
        apolo_passed_config: The Apolo passed config string

    Raises:
        click.BadParameter: If validation fails or client cannot be created
    """
    # Case 1: Token provided but URL missing
    if apolo_api_token and not apolo_api_url:
        err = (
            "When --apolo-api-token is provided, you must also provide --apolo-api-url"
        )
        raise click.BadParameter(err)

    # Case 2: Both token and passed_config are null
    if not apolo_api_token and not apolo_passed_config:
        logger.info(
            "No explicit auth params provided, attempting to use default client"
        )
        try:
            # Try to get a client with default credentials
            async with apolo_sdk.get():
                logger.info("Successfully connected using default credentials")
                return
        except Exception as e:
            err = (
                "Either --apolo-api-token or --apolo-passed-config "
                "must be provided. "
                f"Failed to connect with default credentials: {e}"
            )
            raise click.BadParameter(err) from e

    # Case 3: passed_config provided - set environment variable if needed
    if apolo_passed_config and not os.getenv("APOLO_PASSED_CONFIG"):
        os.environ["APOLO_PASSED_CONFIG"] = apolo_passed_config

    # Case 4: Token provided with URL - will be handled by login_with_token later
