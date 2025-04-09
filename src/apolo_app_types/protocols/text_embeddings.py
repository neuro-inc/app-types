from pydantic import Field

from apolo_app_types import AppInputs, ContainerImage
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputsDeployer,
    AppOutputsDeployer,
    HuggingFaceModel,
    Ingress,
    Preset,
)
from apolo_app_types.protocols.llm import OpenAICompatibleEmbeddingsAPI


class Image(AbstractAppFieldType):
    tag: str


class TextEmbeddingsInferenceAppInputs(AppInputs):
    preset: Preset
    ingress: Ingress
    model: HuggingFaceModel
    container_image: ContainerImage = Field(
        default=ContainerImage(
            repository="ghcr.io/apolo-ai/text-embeddings-inference",
            tag="1.6",
        ),
        description="Container image for the text embeddings inference app.",
        title="Container Image",
    )


class TextEmbeddingsInferenceInputs(AppInputsDeployer):
    preset_name: str
    ingress: Ingress
    model: HuggingFaceModel
    image: Image


class TextEmbeddingsInferenceOutputs(AppOutputsDeployer):
    internal_api: OpenAICompatibleEmbeddingsAPI
    external_api: OpenAICompatibleEmbeddingsAPI | None = None
