import typing as t

import apolo_sdk

from apolo_app_types import AppInputs, LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps import LLMChartValueProcessor
from apolo_app_types.helm.apps.base import BaseChartValueProcessor, AppInputT


def bool_to_string(value: bool) -> str:  # noqa: FBT001
    return "true" if value else "false"


async def _get_compatible_input(
    input_dict: dict[str, t.Any], app_type: AppType
) -> dict[str, t.Any]:
    """
    Get the compatible input for the app, while migrating to the new schema.
    TODO: delete this function once all apps are migrated to the new schema.
    """
    if app_type == AppType.Weaviate:
        return {
            "preset_name": input_dict.get("preset.name", ""),
            "authentication.enabled": bool_to_string(
                input_dict.get("weaviate_params.auth_enabled", False)
            ),
            "backups.enabled": bool_to_string(
                input_dict.get("weaviate_params.backups.enabled", False)
            ),
            **input_dict,
        }
    if app_type == AppType.LLMInference:
        additional_args = {}
        if token := input_dict.get("llm.hugging_face_model.hfToken"):
            additional_args["env"] = {"HUGGING_FACE_HUB_TOKEN": token}

        server_extra_args_converted = {
            (key[4:] if key.startswith("llm.serverExtraArgs") else key): value
            for key, value in input_dict.items()
        }

        return {
            "preset_name": input_dict["preset.name"],
            "model": {
                "modelHFName": input_dict["llm.hugging_face_model.modelHFName"],
                "tokenizerHFName": input_dict.get("llm.tokenizerHFName", ""),
            },
            "llm": {
                "modelHFName": input_dict["llm.hugging_face_model.modelHFName"],
                "tokenizerHFName": input_dict.get("llm.tokenizerHFName", ""),
            },
            **server_extra_args_converted,
            **additional_args,
        }
    if app_type == AppType.StableDiffusion:
        additional_args = {}
        if token := input_dict.get("stable_diffusion.hugging_face_model.hfToken.value"):
            additional_args["env.HUGGING_FACE_HUB_TOKEN"] = token
        if model_files := input_dict.get(
            "stable_diffusion.hugging_face_model.modelFiles"
        ):
            additional_args["model.modelFiles"] = model_files

        return {
            "preset_name": input_dict.get("preset.name", ""),
            "api.replicaCount": input_dict.get("stable_diffusion.replicaCount", 1),
            "api.ingress.enabled": bool_to_string(
                input_dict.get("ingress.enabled", True)
            ),
            "stablestudio.enabled": bool_to_string(
                input_dict.get("stable_diffusion.stablestudio.enabled", False)
            ),
            "stablestudio.preset_name": bool_to_string(
                input_dict["stable_diffusion.stablestudio.preset.name"]
            ),
            "model.modelHFName": bool_to_string(
                input_dict["stable_diffusion.hugging_face_model.modelHFName"]
            ),
            **input_dict,
            **additional_args,
        }

    return input_dict


async def app_type_to_vals(
    input_: AppInputs,
    apolo_client: apolo_sdk.Client,
    app_type: AppType,
    app_name: str,
    namespace: str,
) -> tuple[list[str], dict[str, t.Any]]:
    # Mapping AppType to their respective processor classes
    processor_map: dict[AppType, type[BaseChartValueProcessor[t.Any]]] = {
        AppType.LLMInference: LLMChartValueProcessor,
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
    input_type_map = {
        AppType.LLMInference: LLMInputs,
    }

    if app_type not in input_type_map:
        err_msg = f"App type {app_type} is not supported"
        raise NotImplementedError(err_msg)
    input_ = input_type_map[app_type](**input_dict)

    _, extra_vals = await app_type_to_vals(
        input_,
        apolo_client,
        app_type,
        app_name,
        namespace=namespace,
    )

    return extra_vals
