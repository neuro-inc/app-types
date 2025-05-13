from pydantic import Field

from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputsDeployer,
    AppOutputsDeployer,
    HuggingFaceModel,
    IngressHttp,
    Preset,
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


class TextEmbeddingsInferenceInputs(AppInputsDeployer):
    preset_name: str
    ingress_http: IngressHttp | None = Field(
        default=None,
        title="Enable HTTP Ingress",
    )
    model: HuggingFaceModel
    image: Image


class TextEmbeddingsInferenceOutputs(AppOutputsDeployer):
    internal_api: OpenAICompatibleEmbeddingsAPI
    external_api: OpenAICompatibleEmbeddingsAPI | None = None


class TextEmbeddingsInferenceAppOutputs(AppInputs):
    internal_api: OpenAICompatEmbeddingsAPI | None = None
    external_api: OpenAICompatEmbeddingsAPI | None = None
