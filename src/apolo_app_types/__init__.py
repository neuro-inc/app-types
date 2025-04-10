from apolo_app_types.protocols.apolo_deploy import ApoloDeployInputs, ApoloDeployOutputs
from apolo_app_types.protocols.common import (
    ApoloFilesMount,
    ApoloSecret,
    AppInputs,
    AppInputsDeployer,
    AppOutputs,
    AppOutputsDeployer,
    BasicAuth,
    Bucket,
    Env,
    HuggingFaceModel,
    OptionalStrOrSecret,
    StrOrSecret,
)
from apolo_app_types.protocols.custom_deployment import (
    Container,
    ContainerImage,
    CustomDeploymentInputs,
    CustomDeploymentOutputs,
)
from apolo_app_types.protocols.dify import (
    DifyApi,
    DifyInputs,
    DifyOutputs,
    DifyProxy,
    DifyWeb,
    DifyWorker,
)
from apolo_app_types.protocols.dockerhub import (
    DockerConfigModel,
    DockerHubInputs,
    DockerHubOutputs,
)
from apolo_app_types.protocols.fooocus import (
    FooocusAppInputs,
    FooocusInputs,
    FooocusOutputs,
)
from apolo_app_types.protocols.huggingface_cache import (
    HuggingFaceCacheInputs,
    HuggingFaceCacheOutputs,
)
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
from apolo_app_types.protocols.mlflow import MLFlowAppInputs, MLFlowAppOutputs
from apolo_app_types.protocols.postgres import (
    CrunchyPostgresOutputs,
    CrunchyPostgresUserCredentials,
    PGBouncer,
    PostgresConfig,
    PostgresInputs,
    PostgresOutputs,
)
from apolo_app_types.protocols.private_gpt import PrivateGPTInputs, PrivateGPTOutputs
from apolo_app_types.protocols.pycharm import PycharmInputs, PycharmOutputs
from apolo_app_types.protocols.shell import ShellInputs, ShellOutputs
from apolo_app_types.protocols.spark_job import SparkJobInputs, SparkJobOutputs
from apolo_app_types.protocols.stable_diffusion import (
    SDModel,
    SDOutputs,
    StableDiffusionInputs,
    StableDiffusionOutputs,
    TextToImgAPI,
)
from apolo_app_types.protocols.text_embeddings import (
    TextEmbeddingsInferenceAppInputs,
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
    "MLFlowAppInputs",
    "MLFlowAppOutputs",
    "PostgresInputs",
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
    "ApoloSecret",
    "StrOrSecret",
    "OptionalStrOrSecret",
    "StableDiffusionOutputs",
    "HuggingFaceModel",
    "VLLMOutputsV2",
    "AppInputsDeployer",
    "PGBouncer",
    "PostgresConfig",
    "DockerHubInputs",
    "DockerHubOutputs",
    "DockerConfigModel",
    "ApoloFilesMount",
    "HuggingFaceCacheInputs",
    "HuggingFaceCacheOutputs",
    "CustomDeploymentInputs",
    "CustomDeploymentOutputs",
    "ContainerImage",
    "Container",
    "Env",
    "AppOutputsDeployer",
    "PostgresOutputs",
    "SparkJobInputs",
    "SparkJobOutputs",
    "FooocusAppInputs",
    "ApoloFilesMount",
    "Bucket",
    "TextEmbeddingsInferenceAppInputs",
]
