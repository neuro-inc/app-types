from pydantic import BaseModel, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    HuggingFaceModel,
    Ingress,
    Preset,
)
from apolo_app_types.protocols.common.networking import RestAPI


class LLMApi(BaseModel):
    replicas: int | None = Field(  # noqa: N815
        default=None,
        description="Replicas count.",
        title="API replicas count",
    )
    preset_name: str = Field(  # noqa: N815
        ...,
        description="The name of the preset.",
        title="Preset name",
    )


class LLMModel(BaseModel):
    hugging_face_model: HuggingFaceModel = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )
    tokenizerHFName: str = Field(  # noqa: N815
        ...,
        description="The name of the tokenizer associated with the Hugging Face model.",
        title="Hugging Face Tokenizer Name",
    )
    serverExtraArgs: list[str] = Field(  # noqa: N815
        default_factory=list,
        description="Extra arguments to pass to the server.",
        title="Server Extra Arguments",
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
    preset: Preset
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


class VLLMOutputsV2(AppOutputs):
    chat_internal_api: RestAPI | None = None
    chat_external_api: RestAPI | None = None
    embeddings_internal_api: RestAPI | None = None
    embeddings_external_api: RestAPI | None = None
    hf_model: HuggingFaceModel | None = None
    tokenizer_name: str | None = None
    api_key: str | None = None
