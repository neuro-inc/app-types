import logging
import typing as t

import httpx

from apolo_app_types.outputs.llm import get_llm_inference_outputs


logger = logging.getLogger()


async def post_outputs(api_url: str, api_token: str, outputs: dict[str, t.Any]) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            headers={"Authorization": f"Bearer {api_token}"},
            json=outputs,
        )
        logger.info("API response status code: %s", response.status_code)


async def update_app_outputs(helm_outputs: dict[str, t.Any]) -> None:
    app_type = helm_outputs["PLATFORM_APPS_APP_TYPE"]
    platform_apps_url = helm_outputs["PLATFORM_APPS_URL"]
    platform_apps_token = helm_outputs["PLATFORM_APPS_TOKEN"]
    try:
        if app_type == "llm":
            conv_outputs = await get_llm_inference_outputs(helm_outputs)
        else:
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
