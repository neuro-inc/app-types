from pydantic import BaseModel

from apolo_app_types.common import AppInputs, AppOutputs, Ingress


class LLMApi(BaseModel):
    replicas: int | None
    preset_name: str


class LLMModel(BaseModel):
    model_hf_name: str
    tokenizer_hf_name: str
    api: LLMApi


class Worker(BaseModel):
    replicas: int | None
    preset_name: str


class Proxy(BaseModel):
    preset_name: str


class Web(BaseModel):
    replicas: int | None
    preset_name: str


class LLMInputs(AppInputs):
    preset_name: str
    ingress: Ingress
    model: LLMModel


class OpenAICompatibleAPI(AppOutputs):
    model_name: str
    host: str
    port: str
    api_base: str
    tokenizer_name: str | None = None
    api_key: str | None = None


class OpenAICompatibleEmbeddingsAPI(OpenAICompatibleAPI):
    @property
    def endpoint_url(self) -> str:
        return self.api_base + "/embeddings"


class OpenAICompatibleChatAPI(OpenAICompatibleAPI):
    @property
    def endpoint_url(self) -> str:
        return self.api_base + "/chat"


class OpenAICompatibleCompletionsAPI(OpenAICompatibleChatAPI):
    @property
    def endpoint_url(self) -> str:
        return self.api_base + "/completions"


class VLLMOutputs(AppOutputs):
    chat_internal_api: OpenAICompatibleChatAPI | None
    chat_external_api: OpenAICompatibleChatAPI | None
    embeddings_internal_api: OpenAICompatibleEmbeddingsAPI | None
    embeddings_external_api: OpenAICompatibleEmbeddingsAPI | None
