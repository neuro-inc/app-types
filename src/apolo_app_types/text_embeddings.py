from apolo_app_types.common import AppOutputs
from apolo_app_types.llm import OpenAICompatibleEmbeddingsAPI


class TextEmbeddingsInferenceOutputs(AppOutputs):
    internal_api: OpenAICompatibleEmbeddingsAPI
    external_api: OpenAICompatibleEmbeddingsAPI | None = None
