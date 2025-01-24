import logging
import typing as t
import httpx

from apolo_app_types.outputs.llm import get_llm_inference_outputs


logger = logging.getLogger()


async def update_api(api_url: str, api_token: str, outputs: dict) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            headers={"Authorization": f"Bearer {api_token}"},
            json=outputs,
        )
        logger.info(f"API response: {response.status_code}")



async def update_app_outputs(helm_outputs: dict[str, t.Any]) -> None:
    platform_apps_url = helm_outputs["platform_apps_url"]
    platform_apps_token = helm_outputs["platform_apps_token"]
    try:
        conv_outputs = await get_llm_inference_outputs(helm_outputs)
        await update_api(
            platform_apps_url,
            platform_apps_token,
            conv_outputs,
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}")
