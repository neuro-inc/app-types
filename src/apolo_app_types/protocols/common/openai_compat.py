from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.hugging_face import (
    HF_SCHEMA_EXTRA,
    HuggingFaceModel,
)
from apolo_app_types.protocols.common.networking import (
    RestAPI,
)
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class OpenAICompatChatAPI(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible Chat API",
            description="Configuration for OpenAI compatible chat API.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    api_base_path: str = "/v1"
    # used to distinguish between different types of APIs (chat, embeddings, etc)
    openai_api_type: Literal["chat"] = "chat"
    endpoint_url: Literal["/v1/chat"] = "/v1/chat"
    hf_model: HuggingFaceModel | None = Field(
        default=None,
        json_schema_extra=HF_SCHEMA_EXTRA.as_json_schema_extra(),
    )


class OpenAICompatEmbeddingsAPI(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible Embeddings API",
            description="Configuration for OpenAI compatible embeddings API.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    api_base_path: str = "/v1"
    # used to distinguish between different types of APIs (chat, embeddings, etc)
    openai_api_type: Literal["embeddings"] = "embeddings"
    endpoint_url: Literal["/v1/embeddings"] = "/v1/embeddings"
    hf_model: HuggingFaceModel | None = Field(
        default=None,
        json_schema_extra=HF_SCHEMA_EXTRA.as_json_schema_extra(),
    )


class OpenAICompatCapability(StrEnum):
    CHAT = "chat"
    COMPLETIONS = "completions"
    RESPONSES = "responses"
    EMBEDDINGS = "embeddings"
    RERANK = "rerank"
    SPEECH = "speech"
    TRANSCRIPTION = "transcription"
    IMAGE_GENERATION = "image_generation"


class OpenAICompatModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible Model",
            description="A model served by an OpenAI compatible API.",
        ).as_json_schema_extra(),
    )
    name: str = Field(
        ...,
        min_length=1,
        json_schema_extra=SchemaExtraMetadata(
            title="Model Name",
            description="Name to request the model by.",
        ).as_json_schema_extra(),
    )
    capabilities: list[str] = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Capabilities",
            description="Endpoints that serve the model, such as chat, "
            "embeddings, rerank or speech. Other values can appear.",
        ).as_json_schema_extra(),
    )


class OpenAICompatAPI(RestAPI):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenAI Compatible API",
            description="OpenAI compatible API that serves several models.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    api_base_path: str = "/v1"
    models: list[OpenAICompatModel] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Models",
            description="Models the API serves, with the endpoints of each.",
        ).as_json_schema_extra(),
    )

    def get_model_names(self, capability: str) -> list[str]:
        return [model.name for model in self.models if capability in model.capabilities]


def get_api_base_url(
    api: OpenAICompatChatAPI | OpenAICompatEmbeddingsAPI | OpenAICompatAPI,
) -> str:
    return f"{api.protocol}://{api.host}:{api.port}{api.api_base_path}"
