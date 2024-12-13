from apolo_app_types.common import AppOutputs


class OpenAICompatibleEmbeddingsAPI(AppOutputs):
    model_name: str
    host: str
    port: str
    api_base: str
    tokenizer_name: str | None = None
    api_key: str | None = None


class TextEmbeddingsInferenceOutputs(AppOutputs):
    internal_api: OpenAICompatibleEmbeddingsAPI
    external_api: OpenAICompatibleEmbeddingsAPI | None
