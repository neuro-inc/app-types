import typing as t

from apolo_app_types.outputs.common import (
    INSTANCE_LABEL,
    get_internal_external_web_urls,
)
from apolo_app_types.protocols.common.networking import HttpApi, ServiceAPI
from apolo_app_types.protocols.fooocus import FooocusAppOutputs


async def get_fooocus_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    labels = {"application": "fooocus", INSTANCE_LABEL: app_instance_id}
    internal_web_app_url, external_web_app_url = await get_internal_external_web_urls(
        labels
    )
    return FooocusAppOutputs(
        app_url=ServiceAPI[HttpApi](
            internal_url=internal_web_app_url,
            external_url=external_web_app_url,
        )
        if internal_web_app_url or external_web_app_url
        else None,
    ).model_dump()
