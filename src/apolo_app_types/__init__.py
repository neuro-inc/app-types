from apolo_app_types.common import AppInputs, AppOutputs
from apolo_app_types.dify import (
    DifyApi,
    DifyInputs,
    DifyOutputs,
    DifyProxy,
    DifyWeb,
    DifyWorker,
)
from apolo_app_types.fooocus import FooocusInputs, FooocusOutputs
from apolo_app_types.jupyter import JupyterInputs, JupyterOutputs
from apolo_app_types.llm import LLMInputs, VLLMOutputs
from apolo_app_types.mlflow import MLFlowInputs, MLFlowOutputs
from apolo_app_types.postgres import CrunchyPostgresInputs, CrunchyPostgresOutputs
from apolo_app_types.pycharm import PycharmInputs, PycharmOutputs
from apolo_app_types.shell import ShellInputs, ShellOutputs
from apolo_app_types.stable_diffusion import SDInputs, SDOutputs
from apolo_app_types.text_embeddings import (
    TextEmbeddingsInferenceInputs,
    TextEmbeddingsInferenceOutputs,
)
from apolo_app_types.vscode import VSCodeInputs, VSCodeOutputs
from apolo_app_types.weaviate import WeaviateInputs, WeaviateOutputs


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
