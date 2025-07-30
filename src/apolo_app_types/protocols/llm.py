from pydantic import Field, model_validator

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
from apolo_app_types.protocols.common.autoscaling import AutoscalingKedaHTTP
from apolo_app_types.protocols.common.hugging_face import HF_SCHEMA_EXTRA
from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)


class LLMApi(AbstractAppFieldType):
    replicas: int | None = Field(  # noqa: N815
        default=None,
        gt=0,
        description="Replicas count.",
        title="API replicas count",
    )
    preset_name: str = Field(  # noqa: N815
        ...,
        description="The name of the preset.",
        title="Preset name",
    )


class Worker(AbstractAppFieldType):
    replicas: int = Field(default=1, gt=0)
    preset_name: str


class Proxy(AbstractAppFieldType):
    preset_name: str


class Web(AbstractAppFieldType):
    replicas: int = Field(default=1, gt=0)
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
    hugging_face_model: HuggingFaceModel = Field(
        ...,
        json_schema_extra=HF_SCHEMA_EXTRA.model_copy(
            update={
                "meta_type": SchemaMetaType.INLINE,
            }
        ).as_json_schema_extra(),
    )  # noqa: N815
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
            "to pass to the server (see VLLM doc, e.g. --max-model-len=131072).",
        ).as_json_schema_extra(),
    )
    extra_env_vars: list[Env] = Field(  # noqa: N815
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Extra Environment Variables",
            description=(
                "Additional environment variables to inject into the container. "
                "These will override any existing environment variables "
                "with the same name."
            ),
        ).as_json_schema_extra(),
    )
    cache_config: HuggingFaceCache | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Cache Config", description="Configure Hugging Face cache."
        ).as_json_schema_extra(),
    )
    http_autoscaling: AutoscalingKedaHTTP | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Autoscaling",
            description="Configure autoscaling based on HTTP request rate."
            " If you enable this, "
            "please ensure that cache config "
            "is enabled as well.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    @model_validator(mode="after")
    def check_autoscaling_requires_cache(self) -> "LLMInputs":
        if self.http_autoscaling and not self.cache_config:
            msg = "If HTTP autoscaling is enabled, cache_config must also be set."
            raise ValueError(msg)
        return self


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


class VLLMOutputsV2(AppOutputs):
    chat_internal_api: OpenAICompatChatAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Internal Chat API",
            description="Internal Chat API compatible with "
            "OpenAI standard for seamless integration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    chat_external_api: OpenAICompatChatAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External Chat API",
            description="External Chat API compatible with OpenAI standard.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    embeddings_internal_api: OpenAICompatEmbeddingsAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Internal Embeddings API",
            description="Internal Embeddings API compatible with OpenAI "
            "standard for seamless integration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    embeddings_external_api: OpenAICompatEmbeddingsAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External Embeddings API",
            description="External Embeddings API compatible with OpenAI standard.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    hugging_face_model: HuggingFaceModel
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
            "to pass to the server (see VLLM doc, e.g. --max-model-len=131072).",
        ).as_json_schema_extra(),
    )
    llm_api_key: str | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="LLM Api Key",
            description="LLM Key for the API",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
