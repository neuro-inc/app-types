from pydantic import BaseModel, Field

from apolo_app_types.common import AppInputs, AppOutputs, Ingress


class LLMApi(BaseModel):
    replicas: int | None = Field(  # noqa: N815
        default=None,  # Required field
        description="Replicas count.",
        title="API replicas count",
    )
    preset_name: str = Field(  # noqa: N815
        ...,  # Required field
        description="The name of the preset.",
        title="Preset name",
    )


class LLMModel(BaseModel):
    modelHFName: str = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model to use.",
        title="Hugging Face Model Name",
    )
    tokenizerHFName: str = Field(  # noqa: N815
        ...,  # Required field
        description="The name of the tokenizer associated with the Hugging Face model.",
        title="Hugging Face Tokenizer Name",
    )
    api: LLMApi | None = Field(
        default=None,
        description="An optional LLMApi object to use for connecting to the model.",
        title="API Connection",
    )


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
    llm: LLMModel


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
