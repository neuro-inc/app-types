from pydantic import BaseModel

from apolo_app_types.llm import OpenAICompatibleEmbeddingsAPI
from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    HuggingFaceModel,
    Ingress,
)


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
