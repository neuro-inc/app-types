from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppOutputs,
    AppOutputsDeployer,
    HuggingFaceCache,
    HuggingFaceModel,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)


class LLMApi(AbstractAppFieldType):
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


class LLMModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LLM",
            description="Configure VLLM.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    hugging_face_model: HuggingFaceModel  # noqa: N815
    tokenizer_hf_name: str = Field(  # noqa: N815
        "",
        json_schema_extra=SchemaExtraMetadata(
            description="Set the name of the tokenizer "
            "associated with the Hugging Face model.",
            title="Hugging Face Tokenizer Name",
        ).as_json_schema_extra(),
    )
    server_extra_args: list[str] = Field(  # noqa: N815
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Server Extra Arguments",
            description="Configure extra arguments "
            "to pass to the server (see VLLM doc).",
        ).as_json_schema_extra(),
    )


class Worker(AbstractAppFieldType):
    replicas: int | None
    preset_name: str


class Proxy(AbstractAppFieldType):
    preset_name: str


class Web(AbstractAppFieldType):
    replicas: int | None
    preset_name: str


class LLMInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Public HTTP Ingress",
            description="Enable access to your application"
            " over the internet using HTTPS.",
        ).as_json_schema_extra(),
    )
    llm: LLMModel
    cache_config: HuggingFaceCache | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Cache Config", description="Configure Hugging Face cache."
        ).as_json_schema_extra(),
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


class LLMApiKey(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Integration API key",
            description="Configuration for LLM Api key.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    key: str | None = None


class VLLMOutputsV2(AppOutputs):
    chat_internal_api: OpenAICompatChatAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Chat Internal API",
            description="Chat Internal API ",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    chat_external_api: OpenAICompatChatAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Chat External API",
            description="Chat External API description",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    embeddings_internal_api: OpenAICompatEmbeddingsAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Embeddings Internal API",
            description="Embeddings Internal API description",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    embeddings_external_api: OpenAICompatEmbeddingsAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Embeddings External API",
            description="Embeddings External API",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    llm: LLMModel | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Model Details",
            description="LLM Model Details",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    llm_api_key: LLMApiKey | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Api Key",
            description="LLM Key for the API",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
