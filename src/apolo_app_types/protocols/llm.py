from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppOutputs,
    AppOutputsDeployer,
    HuggingFaceCache,
    HuggingFaceModel,
    Ingress,
    Preset,
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.networking import RestAPI


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
            description="Configuration for LLM.",
        ).as_json_schema_extra(),
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
    ingress: Ingress
    llm: LLMModel
    cache_config: HuggingFaceCache | None = None


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


class LLMSpecific(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Server Details",
            description="Configuration details of the LLM server.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    tokenizer_name: str | None = None
    api_key: str | None = None


class VLLMOutputsV2(AppOutputs):
    chat_internal_api: RestAPI | None = None
    chat_external_api: RestAPI | None = None
    embeddings_internal_api: RestAPI | None = None
    embeddings_external_api: RestAPI | None = None
    hf_model: HuggingFaceModel | None = None
    llm_specific: LLMSpecific | None = None
