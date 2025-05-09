import logging
import typing as t

import httpx

from apolo_app_types.app_types import AppType
from apolo_app_types.outputs.custom_deployment import get_custom_deployment_outputs
from apolo_app_types.outputs.dify import get_dify_outputs
from apolo_app_types.outputs.dockerhub import get_dockerhub_outputs
from apolo_app_types.outputs.fooocus import get_fooocus_outputs
from apolo_app_types.outputs.huggingface_cache import (
    get_app_outputs as get_huggingface_cache_outputs,
)
from apolo_app_types.outputs.jupyter import get_jupyter_outputs
from apolo_app_types.outputs.llm import get_llm_inference_outputs
from apolo_app_types.outputs.mlflow import get_mlflow_outputs
from apolo_app_types.outputs.postgres import get_postgres_outputs
from apolo_app_types.outputs.privategpt import get_privategpt_outputs
from apolo_app_types.outputs.shell import get_shell_outputs
from apolo_app_types.outputs.spark_job import get_spark_job_outputs
from apolo_app_types.outputs.stable_diffusion import get_stable_diffusion_outputs
from apolo_app_types.outputs.tei import get_tei_outputs
from apolo_app_types.outputs.utils.discovery import load_app_postprocessor
from apolo_app_types.outputs.vscode import get_vscode_outputs
from apolo_app_types.outputs.weaviate import get_weaviate_outputs


logger = logging.getLogger()


async def post_outputs(api_url: str, api_token: str, outputs: dict[str, t.Any]) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            headers={"Authorization": f"Bearer {api_token}"},
            json={"output": outputs},
        )
        logger.info(
            "API response status code: %s, body: %s",
            response.status_code,
            response.text,
        )


async def update_app_outputs(  # noqa: C901
    helm_outputs: dict[str, t.Any],
    app_output_processor_type: str | None = None,
    apolo_apps_url: str | None = None,
    apolo_apps_token: str | None = None,
    apolo_app_type: str | None = None,
) -> bool:
    app_type = apolo_app_type or helm_outputs["PLATFORM_APPS_APP_TYPE"]
    platform_apps_url = apolo_apps_url or helm_outputs["PLATFORM_APPS_URL"]
    platform_apps_token = apolo_apps_token or helm_outputs["PLATFORM_APPS_TOKEN"]
    try:
        match app_type:
            case AppType.LLMInference:
                conv_outputs = await get_llm_inference_outputs(helm_outputs)
            case AppType.StableDiffusion:
                conv_outputs = await get_stable_diffusion_outputs(helm_outputs)
            case AppType.Weaviate:
                conv_outputs = await get_weaviate_outputs(helm_outputs)
            case AppType.DockerHub:
                conv_outputs = await get_dockerhub_outputs(helm_outputs)
            case AppType.PostgreSQL:
                conv_outputs = await get_postgres_outputs(helm_outputs)
            case AppType.HuggingFaceCache:
                conv_outputs = await get_huggingface_cache_outputs(helm_outputs)
            case AppType.CustomDeployment:
                conv_outputs = await get_custom_deployment_outputs(helm_outputs)
            case AppType.SparkJob:
                conv_outputs = await get_spark_job_outputs(helm_outputs)
            case AppType.TextEmbeddingsInference:
                conv_outputs = await get_tei_outputs(helm_outputs)
            case AppType.Fooocus:
                conv_outputs = await get_fooocus_outputs(helm_outputs)
            case AppType.MLFlow:
                conv_outputs = await get_mlflow_outputs(helm_outputs)
            case AppType.Jupyter:
                conv_outputs = await get_jupyter_outputs(helm_outputs)
            case AppType.VSCode:
                conv_outputs = await get_vscode_outputs(helm_outputs)
            case AppType.PrivateGPT:
                conv_outputs = await get_privategpt_outputs(helm_outputs)
            case AppType.Shell:
                conv_outputs = await get_shell_outputs(helm_outputs)
            case AppType.Dify:
                conv_outputs = await get_dify_outputs(helm_outputs)
            case _:
                # Try loading application postprocessor defined in the app repo
                postprocessor = load_app_postprocessor(
                    app_id=app_type,
                    exact_type_name=app_output_processor_type,
                )
                if not postprocessor:
                    err_msg = (
                        f"Unsupported app type: {app_type} "
                        f"({app_output_processor_type}) for posting outputs"
                    )
                    raise ValueError(err_msg)
                conv_outputs = await postprocessor().generate_outputs(helm_outputs)
        logger.info("Outputs: %s", conv_outputs)

        await post_outputs(
            platform_apps_url,
            platform_apps_token,
            conv_outputs,
        )
    except Exception as e:
        logger.error("An error occurred: %s", e)
        return False
    return True
