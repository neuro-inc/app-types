import logging
import typing as t

from apolo_app_types import VSCodeAppOutputs
from apolo_app_types.outputs.common import (
    INSTANCE_LABEL,
    get_internal_external_web_urls,
)


logger = logging.getLogger()


async def get_vscode_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    labels = {"application": "vscode", INSTANCE_LABEL: app_instance_id}
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )
    outputs = VSCodeAppOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
    )
    return outputs.model_dump()
