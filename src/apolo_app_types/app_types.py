import enum

from apolo_app_types import StableDiffusionInputs
from apolo_app_types.protocols.common import AppInputs
from apolo_app_types.protocols.dockerhub import DockerHubInputs
from apolo_app_types.protocols.huggingface_cache import (
    HuggingFaceCacheInputs,
)
from apolo_app_types.protocols.jupyter import JupyterAppInputs
from apolo_app_types.protocols.lightrag import LightRAGAppInputs
from apolo_app_types.protocols.llm import LLMInputs
from apolo_app_types.protocols.mlflow import MLFlowAppInputs
from apolo_app_types.protocols.spark_job import SparkJobInputs
from apolo_app_types.protocols.vscode import VSCodeAppInputs
from apolo_app_types.protocols.weaviate import WeaviateInputs


class AppType(enum.StrEnum):
    PostgreSQL = "postgresql"
    TextEmbeddingsInference = "text-embeddings-inference"
    LLMInference = "llm-inference"
    PrivateGPT = "private-gpt"
    Dify = "dify"
    StableDiffusion = "stable-diffusion"
    Weaviate = "weaviate"
    LightRAG = "lightrag"
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
    ServiceDeployment = "service-deployment"
    SparkJob = "spark-job"
    Superset = "superset"

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
        # Mapping from input types to app types to reduce complexity
        input_type_mapping = {
            LLMInputs: AppType.LLMInference,
            WeaviateInputs: AppType.Weaviate,
            LightRAGAppInputs: AppType.LightRAG,
            StableDiffusionInputs: AppType.StableDiffusion,
            DockerHubInputs: AppType.DockerHub,
            HuggingFaceCacheInputs: AppType.HuggingFaceCache,
            SparkJobInputs: AppType.SparkJob,
            MLFlowAppInputs: AppType.MLFlow,
            VSCodeAppInputs: AppType.VSCode,
            JupyterAppInputs: AppType.Jupyter,
        }

        input_type = type(inputs)
        if input_type in input_type_mapping:
            return input_type_mapping[input_type]

        error_message = f"Unsupported input type: {input_type.__name__}"
        raise ValueError(error_message)
