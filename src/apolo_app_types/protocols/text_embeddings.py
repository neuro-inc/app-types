from pydantic import Field

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputsDeployer,
    AppOutputsDeployer,
    HuggingFaceModel,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.openai_compat import OpenAICompatEmbeddingsAPI
from apolo_app_types.protocols.llm import OpenAICompatibleEmbeddingsAPI


class Image(AbstractAppFieldType):
    tag: str


class TextEmbeddingsInferenceAppInputs(AppInputs):
    preset: Preset
    ingress_http: IngressHttp | None = Field(
        default=None,
        title="Enable HTTP Ingress",
    )
    model: HuggingFaceModel
    server_extra_args: list[str] = Field(  # noqa: N815
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Server Extra Arguments",
            description="Configure extra arguments "
            "to pass to the server (see TEI doc, e.g. --max-client-batch-size=1024).",
        ).as_json_schema_extra(),
    )


class TextEmbeddingsInferenceInputs(AppInputsDeployer):
    preset_name: str
    ingress_http: IngressHttp | None = Field(
        default=None,
        title="Enable HTTP Ingress",
    )
    model: HuggingFaceModel
    image: Image
    server_extra_args: list[str] = Field(  # noqa: N815
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Server Extra Arguments",
            description="Configure extra arguments "
            "to pass to the server (see TEI doc, e.g. --max-client-batch-size=1024).",
        ).as_json_schema_extra(),
    )


class TextEmbeddingsInferenceOutputs(AppOutputsDeployer):
    internal_api: OpenAICompatibleEmbeddingsAPI
    external_api: OpenAICompatibleEmbeddingsAPI | None = None


class TextEmbeddingsInferenceAppOutputs(AppInputs):
    internal_api: OpenAICompatEmbeddingsAPI | None = None
    external_api: OpenAICompatEmbeddingsAPI | None = None
