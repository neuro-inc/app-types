import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import apolo_sdk
import click
from yarl import URL

from apolo_app_types.outputs.update_outputs import update_app_outputs
from apolo_app_types.outputs.utils.discovery import (
    load_app_inputs,
    load_app_preprocessor,
)
from apolo_app_types.schema.schema_dumper import dump_schema_type


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
@click.option(
    "--app-output-processor-type", type=str, envvar="APOLO_APP_OUTPUT_PROCESSOR_TYPE"
)
@click.option(
    "--apolo-app-outputs-endpoint", type=str, envvar="APOLO_APP_OUTPUTS_ENDPOINT"
)
@click.option("--apolo-apps-token", type=str, envvar="APOLO_APPS_TOKEN")
@click.option("--apolo-app-type", type=str, envvar="APOLO_APP_TYPE")
def update_outputs(
    helm_outputs_json: str,
    app_output_processor_type: str | None,
    apolo_app_outputs_endpoint: str | None,
    apolo_apps_token: str | None,
    apolo_app_type: str | None,
) -> None:
    try:
        logger.info("Helm input: %s", helm_outputs_json)
        if helm_outputs_json.startswith("'") and helm_outputs_json.endswith("'"):
            logger.info("Single quotes detected, removing them")
            helm_outputs_json = helm_outputs_json[1:-1]
        helm_outputs_dict = json.loads(helm_outputs_json)
        logger.info("Helm outputs: %s", helm_outputs_dict)
        result = asyncio.run(
            update_app_outputs(
                helm_outputs_dict,
                app_output_processor_type=app_output_processor_type,
                apolo_app_outputs_endpoint=apolo_app_outputs_endpoint,
                apolo_apps_token=apolo_apps_token,
                apolo_app_type=apolo_app_type,
            )
        )
        if not result:
            m = "Failed to run update_app_outputs"
            raise Exception(m)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON input: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("An error occurred: %s", e)
        sys.exit(1)


@cli.command("run-preprocessor", context_settings={"ignore_unknown_options": True})
@click.argument("app_type", type=str)
@click.argument("app_id", type=str)
@click.argument("app_name", type=str)
@click.argument("namespace", type=str)
@click.argument("inputs_json", type=str)
@click.argument("helm_values_path", type=Path)
@click.argument("helm_args_path", type=Path)
@click.argument("apps_secret_name", type=str)
@click.option("--inputs-type", type=str, envvar="APOLO_APP_INPUTS_TYPE")
@click.option("--preprocessor-type", type=str, envvar="APOLO_APP_PREPROCESSOR_TYPE")
@click.option("--apolo-api-url", type=str, envvar="APOLO_API_URL", required=True)
@click.option("--apolo-api-token", type=str, envvar="APOLO_API_TOKEN", required=True)
@click.option("--apolo-org", type=str, envvar="APOLO_ORG", required=True)
@click.option("--apolo-cluster", type=str, envvar="APOLO_CLUSTER", required=True)
@click.option("--apolo-project", type=str, envvar="APOLO_PROJECT", required=True)
def run_preprocessor(
    app_type: str,
    app_id: str,
    app_name: str,
    namespace: str,
    inputs_json: str,
    helm_values_path: Path,
    helm_args_path: Path,
    apps_secret_name: str,
    inputs_type: str | None,
    preprocessor_type: str | None,
    apolo_api_url: str,
    apolo_api_token: str,
    apolo_org: str,
    apolo_cluster: str,
    apolo_project: str,
) -> None:
    # template method, expanded by installing extra application modules
    async def _run_preprocessor() -> None:
        logging.basicConfig(level=logging.DEBUG)
        try:
            inputs_dict = json.loads(inputs_json)
            inputs_class = load_app_inputs(app_type, inputs_type)
            if not inputs_class:
                err_msg = f"Unable to find inputs type for {app_type=}, {inputs_type=}"
                raise ValueError(err_msg)

            loaded_inputs = inputs_class.model_validate(inputs_dict)
            logger.info("Loaded inputs: %s", loaded_inputs)

            preprocessor_class = load_app_preprocessor(app_type, preprocessor_type)
            if not preprocessor_class:
                err_msg = (
                    f"Unable to find preprocessor {app_type=}, {preprocessor_type=}"
                )
                raise ValueError(err_msg)

            await apolo_sdk.login_with_token(
                token=apolo_api_token,
                url=URL(apolo_api_url),
            )
            async with apolo_sdk.get() as client:
                await client.config.switch_org(apolo_org)
                await client.config.switch_cluster(apolo_cluster)
                await client.config.switch_project(apolo_project)

                chart_processor = preprocessor_class(client)
                extra_helm_args = await chart_processor.gen_extra_helm_args()
                extra_vals = await chart_processor.gen_extra_values(
                    input_=loaded_inputs,
                    app_name=app_name,
                    namespace=namespace,
                    app_secrets_name=apps_secret_name,
                    app_id=app_id,
                )
                with helm_values_path.open("w") as f:  # noqa: ASYNC230
                    json.dump(extra_vals, f)
                with helm_args_path.open("w") as f:  # noqa: ASYNC230
                    json.dump(extra_helm_args, f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON input: %s", e)
            sys.exit(1)
        except Exception as e:
            logger.error("An error occurred: %s", e)
            sys.exit(1)

    asyncio.run(_run_preprocessor())


@cli.command("dump-types-schema")
@click.argument("app_package_path", type=Path)
@click.argument("expected_app_type_name", type=str)
@click.argument("exact_type_name", type=str)
@click.argument("output_path", type=Path)
def dump_types_schema(
    app_package_path: Path,
    expected_app_type_name: str,
    exact_type_name: str,
    output_path: Path,
) -> None:
    """Dump the schema of the given application input/output type
    from the given app package.

    Args:
        app_package_path (Path): The path to the application package,
        absolute or relative to the current working directory.
            expected_app_type_name (str): The expected application type name.
        exact_type_name (str): The exact type name to dump the schema for.
        output_path (Path): The path to the output file.

    Raises:
        ValueError: If the package path does not exist or does not contain __init__.py.
        ValueError: If the expected application type name does not match the actual
            application type name.
        ValueError: If the exact type name is not found in the application package.
    """
    dump_schema_type(
        app_package_path=app_package_path,
        expected_app_type_name=expected_app_type_name,
        exact_type_name=exact_type_name,
        output_path=output_path,
    )


if __name__ == "__main__":
    cli()
