import asyncio
import json
import logging
import os
import sys

import click

from apolo_app_types.outputs.update_outputs import update_app_outputs


log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    pass


@cli.command("update-outputs", context_settings={"ignore_unknown_options": True})
@click.argument("helm_outputs_json", type=str)
def update_outputs(
    helm_outputs_json: str,
) -> None:
    try:
        helm_outputs_dict = json.loads(helm_outputs_json)
        logger.info("Helm outputs:", helm_outputs_dict)
        asyncio.run(update_app_outputs(helm_outputs_dict))
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON input: %s", e)
    except Exception as e:
        logger.error("An error occurred: %s", e)


if __name__ == "__main__":
    cli()
