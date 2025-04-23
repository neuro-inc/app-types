from typing import Literal

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.hugging_face import (
    HF_SCHEMA_EXTRA,
    HuggingFaceModel,
)
from apolo_app_types.protocols.common.networking import (
    RestAPI,
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


def get_api_base_url(api: OpenAICompatChatAPI | OpenAICompatEmbeddingsAPI) -> str:
    return f"{api.protocol}://{api.host}:{api.port}{api.api_base_path}"
