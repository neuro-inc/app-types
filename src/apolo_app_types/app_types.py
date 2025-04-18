import enum

from apolo_app_types import StableDiffusionInputs
from apolo_app_types.protocols.common import AppInputs
from apolo_app_types.protocols.dockerhub import DockerHubInputs
from apolo_app_types.protocols.huggingface_cache import (
    HuggingFaceCacheInputs,
)
from apolo_app_types.protocols.llm import LLMInputs
from apolo_app_types.protocols.mlflow import MLFlowAppInputs
from apolo_app_types.protocols.spark_job import SparkJobInputs
from apolo_app_types.protocols.weaviate import WeaviateInputs


class AppType(enum.StrEnum):
    PostgreSQL = "postgresql"
    TextEmbeddingsInference = "text-embeddings-inference"
    LLMInference = "llm-inference"
    PrivateGPT = "private-gpt"
    Dify = "dify"
    StableDiffusion = "stable-diffusion"
    Weaviate = "weaviate"
    Fooocus = "fooocus"
    Jupyter = "jupyter"
    VSCode = "vscode"
    Pycharm = "pycharm"
    MLFlow = "mlflow"
    Shell = "shell"
    ApoloDeploy = "apolo-deploy"
    DockerHub = "dockerhub"
    HuggingFaceCache = "huggingface-cache"
    CustomDeployment = "custom-deployment"
    SparkJob = "spark-job"

    def __repr__(self) -> str:
        return str(self)

    def deploys_as_job(self) -> bool:
        return self in {
            AppType.PrivateGPT,
            AppType.Fooocus,
            AppType.Jupyter,
            AppType.VSCode,
            AppType.Pycharm,
            AppType.MLFlow,
            AppType.Shell,
            AppType.ApoloDeploy,
        }

    def is_appless(self) -> bool:
        return self in {
            AppType.HuggingFaceCache,
        }

    @classmethod
    def from_app_inputs(cls, inputs: AppInputs) -> "AppType":
        if isinstance(inputs, LLMInputs):
            return AppType.LLMInference
        if isinstance(inputs, WeaviateInputs):
            return AppType.Weaviate
        if isinstance(inputs, StableDiffusionInputs):
            return AppType.StableDiffusion
        if isinstance(inputs, DockerHubInputs):
            return AppType.DockerHub
        if isinstance(inputs, HuggingFaceCacheInputs):
            return AppType.HuggingFaceCache
        if isinstance(inputs, SparkJobInputs):
            return AppType.SparkJob
        if isinstance(inputs, MLFlowAppInputs):
            return AppType.MLFlow
        error_message = f"Unsupported input type: {type(inputs).__name__}"
        raise ValueError(error_message)
