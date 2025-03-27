from apolo_app_types.protocols.common import AppInputs, AppOutputs, HuggingFaceCache


class HuggingFaceCacheInputs(AppInputs):
    cache_config: HuggingFaceCache


class HuggingFaceCacheOutputs(AppOutputs):
    cache_config: HuggingFaceCache
