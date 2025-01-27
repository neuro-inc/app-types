import asyncio
import json

import click

from apolo_app_types.outputs.llm import logger
from apolo_app_types.outputs.update_outputs import update_app_outputs


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
        logger.debug("Helm outputs:", helm_outputs_dict)
        asyncio.run(update_app_outputs(helm_outputs_dict))
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON input: %s", e)
    except Exception as e:
        logger.error("An error occurred: %s", e)


if __name__ == "__main__":
    cli()
