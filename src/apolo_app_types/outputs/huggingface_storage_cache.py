import logging
import typing as t

from apolo_app_types.protocols.common.storage import ApoloStoragePath
from apolo_app_types.protocols.huggingface_storage_cache import (
    HuggingFaceStorageCacheModel,
    HuggingFaceStorageCacheOutputs,
)


logger = logging.getLogger(__name__)


async def get_app_outputs(helm_values: dict[str, t.Any]) -> dict[str, t.Any]:
    storage_path = helm_values["storage_path"]
    return HuggingFaceStorageCacheOutputs(
        storage_cache=HuggingFaceStorageCacheModel(
            storage_path=ApoloStoragePath(
                path=storage_path,
            ),
        ),
    ).model_dump()
