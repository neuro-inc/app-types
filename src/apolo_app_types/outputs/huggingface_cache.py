import logging
import typing as t

from apolo_app_types.protocols.common.storage import ApoloFilesPath
from apolo_app_types.protocols.huggingface_cache import (
    HuggingFaceCache,
    HuggingFaceCacheOutputs,
)


logger = logging.getLogger(__name__)


async def get_app_outputs(helm_values: dict[str, t.Any]) -> dict[str, t.Any]:
    storage_path = helm_values["storage_path"]
    return HuggingFaceCacheOutputs(
        cache_config=HuggingFaceCache(
            storage_path=ApoloFilesPath(
                path=storage_path,
            ),
        ),
    ).model_dump()
