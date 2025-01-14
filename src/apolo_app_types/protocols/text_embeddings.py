from pydantic import BaseModel

from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    HuggingFaceModel,
    Ingress,
)
from apolo_app_types.protocols.llm import OpenAICompatibleEmbeddingsAPI


class Image(BaseModel):
    tag: str


class TextEmbeddingsInferenceInputs(AppInputs):
    preset_name: str
    ingress: Ingress
    model: HuggingFaceModel
    image: Image


class TextEmbeddingsInferenceOutputs(AppOutputs):
    internal_api: OpenAICompatibleEmbeddingsAPI
    external_api: OpenAICompatibleEmbeddingsAPI | None = None
