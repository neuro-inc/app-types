import typing as t
from importlib.metadata import version

import apolo_sdk

from apolo_app_types import (
    FooocusAppInputs,
    LightRAGAppInputs,
    LLama4Inputs,
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
from apolo_app_types.helm.apps.bundles.llm import (
    DeepSeekValueProcessor,
    Llama4ValueProcessor,
    MistralValueProcessor,
)
from apolo_app_types.helm.apps.dify import DifyChartValueProcessor
from apolo_app_types.helm.apps.dockerhub import DockerHubModelChartValueProcessor
from apolo_app_types.helm.apps.fooocus import FooocusChartValueProcessor
from apolo_app_types.helm.apps.jupyter import JupyterChartValueProcessor
from apolo_app_types.helm.apps.launchpad import LaunchpadChartValueProcessor
from apolo_app_types.helm.apps.lightrag import LightRAGChartValueProcessor
from apolo_app_types.helm.apps.mlflow import MLFlowChartValueProcessor
from apolo_app_types.helm.apps.openwebui import OpenWebUIChartValueProcessor
from apolo_app_types.helm.apps.postgres import PostgresValueProcessor
from apolo_app_types.helm.apps.privategpt import PrivateGptChartValueProcessor
from apolo_app_types.helm.apps.shell import ShellChartValueProcessor
from apolo_app_types.helm.apps.spark_job import SparkJobValueProcessor
from apolo_app_types.helm.apps.superset import SupersetChartValueProcessor
from apolo_app_types.helm.apps.text_embeddings import TextEmbeddingsChartValueProcessor
from apolo_app_types.helm.apps.vscode import VSCodeChartValueProcessor
from apolo_app_types.helm.apps.weaviate import WeaviateChartValueProcessor
from apolo_app_types.protocols.bundles.llm import (
    DeepSeekR1Inputs,
    MistralInputs,
)
from apolo_app_types.protocols.common import AppInputs
from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs
from apolo_app_types.protocols.dify import DifyAppInputs
from apolo_app_types.protocols.dockerhub import DockerHubInputs
from apolo_app_types.protocols.jupyter import JupyterAppInputs
from apolo_app_types.protocols.launchpad import LaunchpadAppInputs
from apolo_app_types.protocols.mlflow import MLFlowAppInputs
from apolo_app_types.protocols.openwebui import OpenWebUIAppInputs
from apolo_app_types.protocols.private_gpt import PrivateGPTAppInputs
from apolo_app_types.protocols.spark_job import SparkJobInputs
from apolo_app_types.protocols.superset import SupersetInputs
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs
from apolo_app_types.protocols.vscode import VSCodeAppInputs


async def app_type_to_vals(
    input_: AppInputs,
    apolo_client: apolo_sdk.Client,
    app_type: AppType,
    app_name: str,
    namespace: str,
    app_id: str,
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
        AppType.LightRAG: LightRAGChartValueProcessor,
        AppType.MLFlow: MLFlowChartValueProcessor,
        AppType.Jupyter: JupyterChartValueProcessor,
        AppType.TextEmbeddingsInference: TextEmbeddingsChartValueProcessor,
        AppType.PrivateGPT: PrivateGptChartValueProcessor,
        AppType.VSCode: VSCodeChartValueProcessor,
        AppType.Shell: ShellChartValueProcessor,
        AppType.Dify: DifyChartValueProcessor,
        AppType.Superset: SupersetChartValueProcessor,
        AppType.OpenWebUI: OpenWebUIChartValueProcessor,
        AppType.Launchpad: LaunchpadChartValueProcessor,
        AppType.Llama4: Llama4ValueProcessor,
        AppType.DeepSeek: DeepSeekValueProcessor,
        AppType.Mistral: MistralValueProcessor,
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
        app_id=app_id,
        app_type=app_type,
    )

    # Adding post-install hook image version
    try:
        app_types_image_version = "v" + version("apolo-app-types")
    except Exception:
        app_types_image_version = "development"
    extra_vals["appTypesImage"] = {
        "tag": app_types_image_version,
    }

    return extra_helm_args, extra_vals


async def get_installation_vals(
    apolo_client: apolo_sdk.Client,
    input_dict: dict[str, t.Any],
    app_name: str,
    app_type: AppType,
    app_id: str,
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
        AppType.LightRAG: LightRAGAppInputs,
        AppType.MLFlow: MLFlowAppInputs,
        AppType.Jupyter: JupyterAppInputs,
        AppType.TextEmbeddingsInference: TextEmbeddingsInferenceAppInputs,
        AppType.PrivateGPT: PrivateGPTAppInputs,
        AppType.Dify: DifyAppInputs,
        AppType.VSCode: VSCodeAppInputs,
        AppType.Shell: ShellAppInputs,
        AppType.Superset: SupersetInputs,
        AppType.OpenWebUI: OpenWebUIAppInputs,
        AppType.Launchpad: LaunchpadAppInputs,
        AppType.Llama4: LLama4Inputs,
        AppType.DeepSeek: DeepSeekR1Inputs,
        AppType.Mistral: MistralInputs,
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
        app_id=app_id,
    )

    return extra_vals
