import logging
import typing as t

from apolo_app_types import CustomDeploymentOutputs
from apolo_app_types.outputs.common import (
    INSTANCE_LABEL,
    get_internal_external_web_urls,
)


logger = logging.getLogger()


async def get_custom_deployment_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
    labels: dict[str, str] | None = None,
) -> dict[str, t.Any]:
    if not labels:
        labels = {
            "application": "custom-deployment",
            INSTANCE_LABEL: app_instance_id,
        }
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )
    return CustomDeploymentOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
    ).model_dump()
