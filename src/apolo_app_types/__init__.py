from apolo_app_types.protocols.common import AppInputs, AppOutputs
from apolo_app_types.protocols.dify import (
    DifyApi,
    DifyInputs,
    DifyOutputs,
    DifyProxy,
    DifyWeb,
    DifyWorker,
)
from apolo_app_types.protocols.fooocus import FooocusInputs, FooocusOutputs
from apolo_app_types.protocols.jupyter import JupyterInputs, JupyterOutputs
from apolo_app_types.protocols.llm import LLMInputs, VLLMOutputs
from apolo_app_types.protocols.mlflow import MLFlowInputs, MLFlowOutputs
from apolo_app_types.protocols.postgres import (
    CrunchyPostgresInputs,
    CrunchyPostgresOutputs,
)
from apolo_app_types.protocols.pycharm import PycharmInputs, PycharmOutputs
from apolo_app_types.protocols.shell import ShellInputs, ShellOutputs
from apolo_app_types.protocols.stable_diffusion import SDInputs, SDOutputs
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
    "SDInputs",
    "TextEmbeddingsInferenceInputs",
    "TextEmbeddingsInferenceOutputs",
    "WeaviateInputs",
    "WeaviateOutputs",
]
