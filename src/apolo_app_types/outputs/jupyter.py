import logging
import typing as t

from apolo_app_types import JupyterAppOutputs
from apolo_app_types.outputs.common import get_internal_external_web_urls


logger = logging.getLogger()


async def get_jupyter_outputs(
    helm_values: dict[str, t.Any], app_instance_id: str
) -> dict[str, t.Any]:
    labels = {"application": "jupyter", "app.kubernetes.io/instance": app_instance_id}
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )

    return JupyterAppOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
    ).model_dump()
