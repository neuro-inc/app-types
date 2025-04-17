import logging
import typing as t

import httpx

from apolo_app_types.app_types import AppType
from apolo_app_types.outputs.custom_deployment import get_custom_deployment_outputs
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
from apolo_app_types.outputs.spark_job import get_spark_job_outputs
from apolo_app_types.outputs.stable_diffusion import get_stable_diffusion_outputs
from apolo_app_types.outputs.tei import get_tei_outputs
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


async def update_app_outputs(helm_outputs: dict[str, t.Any]) -> bool:  # noqa: C901
    app_type = helm_outputs["PLATFORM_APPS_APP_TYPE"]
    platform_apps_url = helm_outputs["PLATFORM_APPS_URL"]
    platform_apps_token = helm_outputs["PLATFORM_APPS_TOKEN"]
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
            case AppType.PrivateGPT:
                conv_outputs = await get_privategpt_outputs(helm_outputs)
            case _:
                err_msg = f"Unsupported app type: {app_type} for posting outputs"
                raise ValueError(err_msg)
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
