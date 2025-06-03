import logging
import typing as t

from apolo_app_types.protocols.common.storage import ApoloFilesPath
from apolo_app_types.protocols.huggingface_cache import (
    HuggingFaceCache,
    HuggingFaceCacheOutputs,
)


logger = logging.getLogger(__name__)


async def get_app_outputs(
    helm_values: dict[str, t.Any], app_instance_id: str
) -> dict[str, t.Any]:
    storage_uri = helm_values["storage_uri"]
    return HuggingFaceCacheOutputs(
        cache_config=HuggingFaceCache(
            files_path=ApoloFilesPath(
                path=storage_uri,
            ),
        ),
    ).model_dump()
