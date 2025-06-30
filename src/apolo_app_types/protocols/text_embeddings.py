from enum import StrEnum

from pydantic import Field

from apolo_app_types import AppInputs, AppOutputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    HuggingFaceModel,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.hugging_face import HF_SCHEMA_EXTRA
from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.openai_compat import OpenAICompatEmbeddingsAPI


class TextEmbeddingsInferenceArchitecture(StrEnum):
    CPU = "cpu"
    TURING = "turing"
    AMPERE_80 = "ampere-80"
    AMPERE_86 = "ampere-86"
    ADA_LOVELACE = "ada-lovelace"
    HOPPER = "hopper"


class TextEmbeddingsInferenceImageTag(StrEnum):
    CPU = "cpu-1.7"
    TURING = "turing-1.7"
    AMPERE_80 = "1.7"  # Default/main image for A100/A30
    AMPERE_86 = "86-1.7"
    ADA_LOVELACE = "89-1.7"
    HOPPER = "hopper-1.7"


class Image(AbstractAppFieldType):
    tag: str


class TextEmbeddingsInferenceAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp | None = Field(
        default=None,
        title="Enable HTTP Ingress",
    )
    model: HuggingFaceModel = Field(
        ...,
        json_schema_extra=HF_SCHEMA_EXTRA.model_copy(
            update={
                "meta_type": SchemaMetaType.INLINE,
            }
        ).as_json_schema_extra(),
    )
    server_extra_args: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Server Extra Arguments",
            description="Configure extra arguments "
            "to pass to the server (see TEI doc, e.g. --max-client-batch-size=1024).",
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


class TextEmbeddingsInferenceAppOutputs(AppOutputs):
    internal_api: OpenAICompatEmbeddingsAPI | None = None
    external_api: OpenAICompatEmbeddingsAPI | None = None
