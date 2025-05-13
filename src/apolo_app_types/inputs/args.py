import typing as t

import apolo_sdk

from apolo_app_types import (
    FooocusAppInputs,
    LLMInputs,
    PostgresInputs,
    ShellAppInputs,
    StableDiffusionInputs,
    WeaviateInputs,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps import (
    CustomDeploymentChartValueProcessor,
    LLMChartValueProcessor,
    StableDiffusionChartValueProcessor,
)
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.dify import DifyChartValueProcessor
from apolo_app_types.helm.apps.dockerhub import DockerHubModelChartValueProcessor
from apolo_app_types.helm.apps.fooocus import FooocusChartValueProcessor
from apolo_app_types.helm.apps.jupyter import JupyterChartValueProcessor
from apolo_app_types.helm.apps.mlflow import MLFlowChartValueProcessor
from apolo_app_types.helm.apps.postgres import PostgresValueProcessor
from apolo_app_types.helm.apps.privategpt import PrivateGptChartValueProcessor
from apolo_app_types.helm.apps.shell import ShellChartValueProcessor
from apolo_app_types.helm.apps.spark_job import SparkJobValueProcessor
from apolo_app_types.helm.apps.text_embeddings import TextEmbeddingsChartValueProcessor
from apolo_app_types.helm.apps.vscode import VSCodeChartValueProcessor
from apolo_app_types.helm.apps.weaviate import WeaviateChartValueProcessor
from apolo_app_types.protocols.common import AppInputs
from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs
from apolo_app_types.protocols.dify import DifyAppInputs
from apolo_app_types.protocols.dockerhub import DockerHubInputs
from apolo_app_types.protocols.jupyter import JupyterAppInputs
from apolo_app_types.protocols.mlflow import MLFlowAppInputs
from apolo_app_types.protocols.private_gpt import PrivateGPTAppInputs
from apolo_app_types.protocols.spark_job import SparkJobInputs
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs
from apolo_app_types.protocols.vscode import VSCodeAppInputs


async def app_type_to_vals(
    input_: AppInputs,
    apolo_client: apolo_sdk.Client,
    app_type: AppType,
    app_name: str,
    namespace: str,
    app_secrets_name: str,
) -> tuple[list[str], dict[str, t.Any]]:
    # Mapping AppType to their respective processor classes
    processor_map: dict[AppType, type[BaseChartValueProcessor[t.Any]]] = {
        AppType.LLMInference: LLMChartValueProcessor,
        AppType.StableDiffusion: StableDiffusionChartValueProcessor,
        AppType.Weaviate: WeaviateChartValueProcessor,
        AppType.DockerHub: DockerHubModelChartValueProcessor,
        AppType.PostgreSQL: PostgresValueProcessor,
        AppType.CustomDeployment: CustomDeploymentChartValueProcessor,
        AppType.SparkJob: SparkJobValueProcessor,
        AppType.Fooocus: FooocusChartValueProcessor,
        AppType.MLFlow: MLFlowChartValueProcessor,
        AppType.Jupyter: JupyterChartValueProcessor,
        AppType.TextEmbeddingsInference: TextEmbeddingsChartValueProcessor,
        AppType.PrivateGPT: PrivateGptChartValueProcessor,
        AppType.VSCode: VSCodeChartValueProcessor,
        AppType.Shell: ShellChartValueProcessor,
        AppType.Dify: DifyChartValueProcessor,
    }

    processor_class = processor_map.get(app_type)

    if not processor_class:
        err_msg = f"App type {app_type} is not supported"
        raise RuntimeError(err_msg)

    chart_processor = processor_class(apolo_client)
    extra_helm_args = await chart_processor.gen_extra_helm_args()
    extra_vals = await chart_processor.gen_extra_values(
        input_=input_,
        app_name=app_name,
        namespace=namespace,
        app_secrets_name=app_secrets_name,
    )
    return extra_helm_args, extra_vals


async def get_installation_vals(
    apolo_client: apolo_sdk.Client,
    input_dict: dict[str, t.Any],
    app_name: str,
    app_type: AppType,
    namespace: str = "default",
    app_secrets_name: str = "apps-secrets",
) -> dict[str, t.Any]:
    input_type_map: dict[AppType, type[AppInputs]] = {
        AppType.LLMInference: LLMInputs,
        AppType.StableDiffusion: StableDiffusionInputs,
        AppType.Weaviate: WeaviateInputs,
        AppType.DockerHub: DockerHubInputs,
        AppType.PostgreSQL: PostgresInputs,
        AppType.CustomDeployment: CustomDeploymentInputs,
        AppType.SparkJob: SparkJobInputs,
        AppType.Fooocus: FooocusAppInputs,
        AppType.MLFlow: MLFlowAppInputs,
        AppType.Jupyter: JupyterAppInputs,
        AppType.TextEmbeddingsInference: TextEmbeddingsInferenceAppInputs,
        AppType.PrivateGPT: PrivateGPTAppInputs,
        AppType.Dify: DifyAppInputs,
        AppType.VSCode: VSCodeAppInputs,
        AppType.Shell: ShellAppInputs,
    }

    if app_type not in input_type_map:
        err_msg = f"App type {app_type} is not supported"
        raise NotImplementedError(err_msg)
    input_ = input_type_map[app_type].model_validate(input_dict)

    _, extra_vals = await app_type_to_vals(
        input_,
        apolo_client,
        app_type,
        app_name,
        namespace=namespace,
        app_secrets_name=app_secrets_name,
    )

    return extra_vals
