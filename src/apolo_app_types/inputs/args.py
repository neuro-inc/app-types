import typing as t

import apolo_sdk

from apolo_app_types import (
    CrunchyPostgresInputs,
    LLMInputs,
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
from apolo_app_types.helm.apps.dockerhub import DockerHubModelChartValueProcessor
from apolo_app_types.helm.apps.postgres import PostgresValueProcessor
from apolo_app_types.helm.apps.weaviate import WeaviateChartValueProcessor
from apolo_app_types.protocols.common import AppInputsV2
from apolo_app_types.protocols.custom_deployment import CustomDeploymentInputs
from apolo_app_types.protocols.dockerhub import DockerHubInputs


async def app_type_to_vals(
    input_: AppInputsV2,
    apolo_client: apolo_sdk.Client,
    app_type: AppType,
    app_name: str,
    namespace: str,
) -> tuple[list[str], dict[str, t.Any]]:
    # Mapping AppType to their respective processor classes
    processor_map: dict[AppType, type[BaseChartValueProcessor[t.Any]]] = {
        AppType.LLMInference: LLMChartValueProcessor,
        AppType.StableDiffusion: StableDiffusionChartValueProcessor,
        AppType.Weaviate: WeaviateChartValueProcessor,
        AppType.DockerHub: DockerHubModelChartValueProcessor,
        AppType.PostgreSQL: PostgresValueProcessor,
        AppType.CustomDeployment: CustomDeploymentChartValueProcessor,
    }

    processor_class = processor_map.get(app_type)

    if not processor_class:
        err_msg = f"App type {app_type} is not supported"
        raise RuntimeError(err_msg)

    chart_processor = processor_class(apolo_client)
    extra_helm_args = await chart_processor.gen_extra_helm_args()
    extra_vals = await chart_processor.gen_extra_values(
        input_=input_, app_name=app_name, namespace=namespace
    )
    return extra_helm_args, extra_vals


async def get_installation_vals(
    apolo_client: apolo_sdk.Client,
    input_dict: dict[str, t.Any],
    app_name: str,
    app_type: AppType,
    namespace: str = "default",
) -> dict[str, t.Any]:
    input_type_map: dict[AppType, type[AppInputsV2]] = {
        AppType.LLMInference: LLMInputs,
        AppType.StableDiffusion: StableDiffusionInputs,
        AppType.Weaviate: WeaviateInputs,
        AppType.DockerHub: DockerHubInputs,
        AppType.PostgreSQL: CrunchyPostgresInputs,
        AppType.CustomDeployment: CustomDeploymentInputs,
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
    )

    return extra_vals
