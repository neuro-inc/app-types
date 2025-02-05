import logging
import os
import re
import typing as t
from copy import deepcopy

import apolo_sdk
import click
import yaml
from apolo_app_types.helm.apps.ingress import get_ingress_values
from apolo_app_types.protocols.common import Ingress, Preset as PresetType
from apolo_sdk import Preset

logger = logging.getLogger(__name__)


def get_preset(client: apolo_sdk.Client, preset_name: str) -> apolo_sdk.Preset:
    preset = client.config.presets.get(preset_name)
    if not preset:
        msg = f"Preset {preset_name} not exist in cluster {client.config.cluster_name}"
        raise click.ClickException(msg)
    return preset


def preset_to_resources(preset: apolo_sdk.Preset) -> dict[str, t.Any]:
    requests = {
        "cpu": f"{preset.cpu * 1000}m",
        "memory": f"{preset.memory_mb}M",
    }
    if preset.nvidia_gpu:
        requests["nvidia.com/gpu"] = str(preset.nvidia_gpu)
    if preset.amd_gpu:
        requests["amd.com/gpu"] = str(preset.amd_gpu)

    return {"requests": requests, "limits": requests.copy()}


def get_component_values(preset: Preset, preset_name: str) -> dict[str, t.Any]:
    return {
        "labels": {
            "platform.apolo.us/component": "app",
            "platform.apolo.us/preset": preset_name,
        },
        "resources": preset_to_resources(preset),
        "tolerations": preset_to_tolerations(preset),
        "affinity": preset_to_affinity(preset),
    }


def _get_match_expressions(pool_names: list[str]) -> list[dict[str, t.Any]]:
    return [
        {
            "key": "platform.neuromation.io/nodepool",
            "operator": "In",
            "values": pool_names,
        }
    ]


def preset_to_affinity(preset: apolo_sdk.Preset) -> dict[str, t.Any]:
    affinity = {}
    if preset.available_resource_pool_names:
        affinity["nodeAffinity"] = {
            "requiredDuringSchedulingIgnoredDuringExecution": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": _get_match_expressions(
                            list(preset.available_resource_pool_names)
                        )
                    }
                ]
            }
        }
    return affinity


def preset_to_tolerations(preset: apolo_sdk.Preset) -> list[dict[str, t.Any]]:
    tolerations: list[dict[str, t.Any]] = [
        {
            "effect": "NoSchedule",
            "key": "platform.neuromation.io/job",
            "operator": "Exists",
        },
        {
            "effect": "NoExecute",
            "key": "node.kubernetes.io/not-ready",
            "operator": "Exists",
            "tolerationSeconds": 300,
        },
        {
            "effect": "NoExecute",
            "key": "node.kubernetes.io/unreachable",
            "operator": "Exists",
            "tolerationSeconds": 300,
        },
    ]
    if preset.amd_gpu:
        tolerations.append(
            {"effect": "NoSchedule", "key": "amd.com/gpu", "operator": "Exists"}
        )
    if preset.nvidia_gpu:
        tolerations.append(
            {"effect": "NoSchedule", "key": "nvidia.com/gpu", "operator": "Exists"}
        )
    return tolerations


def parse_chart_values_simple(helm_args: list[str]) -> dict[str, t.Any]:
    chart_values = {}
    set_re = re.compile(r"--set[\s+,=](.+?)(?= --set|\s|$)")

    for match in set_re.finditer(" ".join(helm_args)):
        keyvalue = match.group(1).strip()
        key, value = keyvalue.split("=", 1)
        chart_values[key] = value
    return chart_values


# TODO: hack - should define specific input models for each helm app
def get_extra_env_vars_from_job() -> tuple[dict[str, t.Any], list[str]]:
    """
    Get extra env vars from job environment.
    Currently, only HUGGING_FACE_HUB_TOKEN is supported.

    Returns:
        Tuple[dict[str, t.Any], list[str]]: Tuple of extra env vars and secret strings.
    """
    extra_env_vars = {}
    secret_strings = []
    hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
    if hf_token:
        extra_env_vars["HUGGING_FACE_HUB_TOKEN"] = hf_token
        secret_strings.append(hf_token)
    return extra_env_vars, secret_strings


def set_value_from_dot_notation(
    data: dict[str, t.Any], key: str, value: t.Any
) -> dict[str, t.Any]:
    """
    Set value in nested dict using dot notation.

    Args:
        data (dict[str, t.Any]): Nested dict.
        key (str): Dot notation key.
        value (t.Any): Value to set.

    Returns:
        dict[str, t.Any]: Updated nested dict.
    """
    data_ref = data
    keys = key.split(".")
    for k in keys[:-1]:
        data = data.setdefault(k, {})
    data[keys[-1]] = value
    return data_ref


def sanitize_dict_string(
    values: dict[str, t.Any],
    secrets: t.Sequence[str] | None = None,
    keys: t.Sequence[str] | None = None,
) -> str:
    keys = keys or []
    secrets = secrets or []
    values = deepcopy(values)
    for key in keys:
        values = set_value_from_dot_notation(values, key, "****")
    dict_str = yaml.dump(values)
    if len(secrets) > 0:
        sec_re = re.compile(f"({'|'.join(secrets)})")  # noqa: arg-type
        return sec_re.sub("****", dict_str)
    return dict_str


async def gen_extra_values(
    apolo_client: apolo_sdk.Client,
    preset: PresetType,
    ingress: Ingress,
    namespace: str,
) -> dict[str, t.Any]:
    preset_name = preset.name
    if not preset_name:
        logger.warning("No preset_name found in helm args.")
        return {}

    preset = get_preset(apolo_client, preset_name)
    tolerations = preset_to_tolerations(preset)
    affinity = preset_to_affinity(preset)
    resources = preset_to_resources(preset)
    ingress = await get_ingress_values(apolo_client, ingress, namespace)

    # TODO replace this hack with input models for each helm app
    extra_env_vars, secret_strings = get_extra_env_vars_from_job()

    values = {
        "preset_name": preset_name,
        "resources": resources,
        "tolerations": tolerations,
        "affinity": affinity,
        "env": extra_env_vars,
        "ingress": ingress.get("ingress", {}),
    }

    logger.debug(
        "Generated extra values: \n %s",
        sanitize_dict_string(values, secret_strings),
    )

    return values
