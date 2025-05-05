import typing as t

from apolo_app_types import ShellAppOutputs
from apolo_app_types.outputs.common import get_internal_external_web_urls


async def get_shell_outputs(
    helm_values: dict[str, t.Any],
) -> dict[str, t.Any]:
    labels = {"application": "shell"}
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )

    return ShellAppOutputs(
        internal_web_app_url=internal_web_app_url,
        external_web_app_url=external_web_app_url,
    ).model_dump()
