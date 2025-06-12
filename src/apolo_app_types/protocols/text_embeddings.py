from pydantic import Field

from apolo_app_types import AppInputs, AppOutputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    HuggingFaceModel,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.openai_compat import OpenAICompatEmbeddingsAPI


class Image(AbstractAppFieldType):
    tag: str


class TextEmbeddingsInferenceAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp | None = Field(
        default=None,
        title="Enable HTTP Ingress",
    )
    model: HuggingFaceModel
    server_extra_args: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Server Extra Arguments",
            description="Configure extra arguments "
            "to pass to the server (see TEI doc, e.g. --max-client-batch-size=1024).",
        ).as_json_schema_extra(),
    )
    extra_env_vars: dict[str, str] = Field(  # noqa: N815
        default_factory=dict,
        json_schema_extra=SchemaExtraMetadata(
            title="Extra Environment Variables",
            description="Additional environment variables to set for the "
            "container. These will override any existing environment variables "
            "with the same name. (see vLLM doc, e.g. VLLM_USE_V1=0)",
        ).as_json_schema_extra(),
    )


class TextEmbeddingsInferenceAppOutputs(AppOutputs):
    internal_api: OpenAICompatEmbeddingsAPI | None = None
    external_api: OpenAICompatEmbeddingsAPI | None = None
