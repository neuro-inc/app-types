import asyncio
import json
import typing as t

import click

from apolo_app_types.outputs.llm import get_llm_inference_outputs


@click.group()
def cli() -> None:
    pass


@cli.command("update-outputs", context_settings={"ignore_unknown_options": True})
@click.argument("helm_outputs_json", type=str)
def update_outputs(
    helm_outputs_json: str,
) -> None:
    try:
        # Parse the JSON string into a Python dictionary
        helm_outputs_dict = json.loads(helm_outputs_json)
        print("Helm outputs:", helm_outputs_dict)
        asyncio.run(get_llm_inference_outputs(helm_outputs_dict))
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON input: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    cli()
