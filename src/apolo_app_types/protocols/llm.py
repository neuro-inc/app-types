from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    AppOutputsDeployer,
    HuggingFaceModel,
    Ingress,
    Preset,
)
from apolo_app_types.protocols.common.networking import RestAPI
from apolo_app_types.protocols.huggingface_storage_cache import (
    HuggingFaceStorageCacheModel,
)


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
    model_config = ConfigDict(
        json_schema_extra={
            "x-title": "LLM Configuration",
            "x-description": "Configuration for LLM.",
            "x-logo-url": "https://example.com/logo",
        }
    )
    hugging_face_model: HuggingFaceModel = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )
    tokenizer_hf_name: str = Field(  # noqa: N815
        "",
        description="The name of the tokenizer associated with the Hugging Face model.",
        title="Hugging Face Tokenizer Name",
    )
    server_extra_args: list[str] = Field(  # noqa: N815
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
    preset: Preset = Field(
        ...,
        description="Preset to use for LLM instance. "
        "Preferably a preset with GPU resources.",
        title="Resource preset",
    )
    ingress: Ingress = Field(
        ...,
        description="Ingress configuration for the LLM instance.",
        title="Ingress configuration",
    )
    llm: LLMModel = Field(
        ...,
        description="LLM model configuration.",
        title="LLM model configuration",
    )
    storage_cache: HuggingFaceStorageCacheModel | None = Field(
        None,
        description="Configuration for Hugging Face storage cache.",
        title="Hugging Face storage cache configuration",
    )


class OpenAICompatibleAPI(AppOutputsDeployer):
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


class VLLMOutputs(AppOutputsDeployer):
    chat_internal_api: OpenAICompatibleChatAPI | None
    chat_external_api: OpenAICompatibleChatAPI | None
    embeddings_internal_api: OpenAICompatibleEmbeddingsAPI | None
    embeddings_external_api: OpenAICompatibleEmbeddingsAPI | None


class LLMSpecific(BaseModel):
    tokenizer_name: str | None = None
    api_key: str | None = None


class VLLMOutputsV2(AppOutputs):
    chat_internal_api: RestAPI | None = None
    chat_external_api: RestAPI | None = None
    embeddings_internal_api: RestAPI | None = None
    embeddings_external_api: RestAPI | None = None
    hf_model: HuggingFaceModel | None = None
    llm_specific: LLMSpecific | None = None
