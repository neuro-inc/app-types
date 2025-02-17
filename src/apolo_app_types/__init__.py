from apolo_app_types.protocols.apolo_deploy import ApoloDeployInputs, ApoloDeployOutputs
from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    BasicAuth,
    HuggingFaceModel,
    K8sSecret,
    OptionalStrOrSecret,
    StrOrSecret,
)
from apolo_app_types.protocols.common.buckets import Bucket
from apolo_app_types.protocols.custom_app import CustomAppInputs, CustomAppOutputs
from apolo_app_types.protocols.dify import (
    DifyApi,
    DifyInputs,
    DifyOutputs,
    DifyProxy,
    DifyWeb,
    DifyWorker,
)
from apolo_app_types.protocols.fooocus import FooocusInputs, FooocusOutputs
from apolo_app_types.protocols.jupyter import (
    JupyterInputs,
    JupyterOutputs,
    JupyterTypes,
)
from apolo_app_types.protocols.llm import (
    LLMInputs,
    OpenAICompatibleAPI,
    OpenAICompatibleChatAPI,
    OpenAICompatibleCompletionsAPI,
    OpenAICompatibleEmbeddingsAPI,
    VLLMOutputs,
    VLLMOutputsV2,
)
from apolo_app_types.protocols.mlflow import MLFlowInputs, MLFlowOutputs
from apolo_app_types.protocols.postgres import (
    CrunchyPostgresInputs,
    CrunchyPostgresOutputs,
    CrunchyPostgresUserCredentials,
)
from apolo_app_types.protocols.private_gpt import PrivateGPTInputs, PrivateGPTOutputs
from apolo_app_types.protocols.pycharm import PycharmInputs, PycharmOutputs
from apolo_app_types.protocols.shell import ShellInputs, ShellOutputs
from apolo_app_types.protocols.stable_diffusion import (
    SDModel,
    SDOutputs,
    StableDiffusionInputs,
    TextToImgAPI,
)
from apolo_app_types.protocols.text_embeddings import (
    TextEmbeddingsInferenceInputs,
    TextEmbeddingsInferenceOutputs,
)
from apolo_app_types.protocols.vscode import VSCodeInputs, VSCodeOutputs
from apolo_app_types.protocols.weaviate import WeaviateInputs, WeaviateOutputs


__all__ = [
    "AppInputs",
    "AppOutputs",
    "DifyApi",
    "DifyInputs",
    "DifyOutputs",
    "DifyProxy",
    "DifyWeb",
    "DifyWorker",
    "PycharmInputs",
    "PycharmOutputs",
    "VSCodeInputs",
    "VSCodeOutputs",
    "FooocusInputs",
    "FooocusOutputs",
    "JupyterInputs",
    "JupyterOutputs",
    "LLMInputs",
    "VLLMOutputs",
    "MLFlowInputs",
    "MLFlowOutputs",
    "CrunchyPostgresInputs",
    "CrunchyPostgresOutputs",
    "ShellInputs",
    "ShellOutputs",
    "SDOutputs",
    "StableDiffusionInputs",
    "TextEmbeddingsInferenceInputs",
    "TextEmbeddingsInferenceOutputs",
    "WeaviateInputs",
    "WeaviateOutputs",
    "OpenAICompatibleEmbeddingsAPI",
    "OpenAICompatibleAPI",
    "OpenAICompatibleChatAPI",
    "OpenAICompatibleCompletionsAPI",
    "TextToImgAPI",
    "CrunchyPostgresUserCredentials",
    "SDModel",
    "BasicAuth",
    "ApoloDeployInputs",
    "ApoloDeployOutputs",
    "JupyterTypes",
    "PrivateGPTInputs",
    "PrivateGPTOutputs",
    "CustomAppInputs",
    "CustomAppOutputs",
    "K8sSecret",
    "StrOrSecret",
    "OptionalStrOrSecret",
    "Bucket",
    "StableDiffusionInputs",
    "HuggingFaceModel",
    "VLLMOutputsV2",
]
