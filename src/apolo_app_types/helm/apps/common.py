import json
import logging
import os
import re
import typing as t
from copy import deepcopy
from decimal import Decimal

import apolo_sdk
import yaml
from apolo_sdk import Preset
from neuro_config_client import NodePool

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.ingress import (
    get_grpc_ingress_values,
    get_http_ingress_values,
)
from apolo_app_types.protocols.common import (
    ApoloFilesMount,
    IngressGrpc,
    IngressHttp,
    Preset as PresetType,
)
from apolo_app_types.protocols.common.k8s import Port


logger = logging.getLogger(__name__)

APOLO_STORAGE_LABEL = "platform.apolo.us/inject-storage"
APOLO_ORG_LABEL = "platform.apolo.us/org"
APOLO_PROJECT_LABEL = "platform.apolo.us/project"

KEDA_HTTP_PROXY_SERVICE = (
    "keda-add-ons-http-interceptor-proxy.platform.svc.cluster.local"
)


def get_preset(client: apolo_sdk.Client, preset_name: str) -> apolo_sdk.Preset:
    if os.environ.get("ENV") == "local":
        return Preset(
            credits_per_hour=Decimal(1.0),
            cpu=1,
            memory=1024,
            resource_pool_names=("default",),
            available_resource_pool_names=("default",),
        )
    preset = client.config.presets.get(preset_name)
    if not preset:
        msg = f"Preset {preset_name} not exist in cluster {client.config.cluster_name}"
        raise ValueError(msg)
    return preset


def preset_to_resources(preset: apolo_sdk.Preset) -> dict[str, t.Any]:
    requests = {
        "cpu": f"{preset.cpu * 1000}m",
        "memory": f"{preset.memory / (1 << 20):.0f}M",
    }
    if preset.nvidia_gpu and preset.nvidia_gpu.count > 0:
        requests["nvidia.com/gpu"] = str(preset.nvidia_gpu.count)
    if preset.amd_gpu and preset.amd_gpu.count > 0:
        requests["amd.com/gpu"] = str(preset.amd_gpu.count)

    return {"requests": requests, "limits": requests.copy()}


async def get_component_values(preset: Preset, preset_name: str) -> dict[str, t.Any]:
    return {
        "labels": {
            "platform.apolo.us/component": "app",
            "platform.apolo.us/preset": preset_name,
        },
        "resources": preset_to_resources(preset),
        "tolerations": await preset_to_tolerations(preset),
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


async def get_resource_pools(preset: apolo_sdk.Preset) -> list[NodePool]:
    async with apolo_sdk.get() as client:
        pool_types = await client._clusters._client.list_node_pools(client.cluster_name)
        return [p for p in pool_types if p.name in preset.resource_pool_names]


async def preset_to_tolerations(preset: apolo_sdk.Preset) -> list[dict[str, t.Any]]:
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

    try:
        pool_types = await get_resource_pools(preset)
    except Exception as e:
        err = f"Failed to get resource pools: {e}"
        logger.error(err)
        pool_types = []

    if (preset.amd_gpu and preset.amd_gpu.count > 0) or any(
        p.amd_gpu for p in pool_types
    ):
        tolerations.append(
            {"effect": "NoSchedule", "key": "amd.com/gpu", "operator": "Exists"}
        )
    if (preset.nvidia_gpu and preset.nvidia_gpu.count > 0) or any(
        p.nvidia_gpu for p in pool_types
    ):
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
        sec_re = re.compile(f"({'|'.join(secrets)})")
        return sec_re.sub("****", dict_str)
    return dict_str


def gen_apolo_storage_integration_annotations(
    files_mouts: t.Sequence[ApoloFilesMount], client: apolo_sdk.Client
) -> list[dict[str, str]]:
    storage_mount_annotations = []
    for storage_mount in files_mouts:
        storage_uri = storage_mount.storage_uri
        if not storage_uri.is_absolute():
            if not client:
                err_msg = "You must pass client if mounts use relative paths"
                raise ValueError(err_msg)
            storage_uri = storage_uri.get_absolute_path_model(client=client)
        storage_mount_annotations.append(
            {
                "storage_uri": storage_uri.path,
                "mount_path": storage_mount.mount_path.path,
                "mount_mode": storage_mount.mode.mode.value,
            }
        )
    return storage_mount_annotations


def gen_apolo_storage_integration_labels(
    *,
    client: apolo_sdk.Client,
    inject_storage: bool = False,
) -> dict[str, str]:
    if inject_storage:
        return {
            APOLO_STORAGE_LABEL: "true",
            APOLO_ORG_LABEL: client.config.org_name or "",
            APOLO_PROJECT_LABEL: client.config.project_name or "",
        }
    return {}


def append_apolo_storage_integration_annotations(
    current_annotations: dict[str, t.Any],
    files_mounts: t.Sequence[ApoloFilesMount],
    client: apolo_sdk.Client,
) -> dict[str, str]:
    """
    Returns a new dict with the storage annotations appended to the current annotations.
    """
    cur_annot = deepcopy(current_annotations)
    cur_apolo_annotation_str: str | None = cur_annot.get(APOLO_STORAGE_LABEL)
    if cur_apolo_annotation_str:
        current_list = json.loads(cur_apolo_annotation_str)
    else:
        current_list = []

    new_annotations = gen_apolo_storage_integration_annotations(files_mounts, client)
    current_list.extend(new_annotations)
    cur_annot[APOLO_STORAGE_LABEL] = json.dumps(current_list)
    return cur_annot


async def gen_extra_values(
    apolo_client: apolo_sdk.Client,
    preset_type: PresetType,
    app_id: str,
    app_type: AppType,
    ingress_http: IngressHttp | None = None,
    ingress_grpc: IngressGrpc | None = None,
    namespace: str | None = None,
    port_configurations: list[Port] | None = None,
    component_name: str | None = None,
) -> dict[str, t.Any]:
    preset_name = preset_type.name
    if not preset_name:
        logger.warning("No preset_name found in helm args.")
        return {}

    preset = get_preset(apolo_client, preset_name)
    tolerations_vals = await preset_to_tolerations(preset)
    affinity_vals = preset_to_affinity(preset)
    resources_vals = preset_to_resources(preset)
    ingress_vals: dict[str, t.Any] = {}
    http_ingress_conf: dict[str, t.Any] | None = None
    grpc_ingress_conf: dict[str, t.Any] | None = None

    if ingress_http or ingress_grpc:
        if not namespace:
            exception_msg = "Namespace is required when ingress is provided."
            raise ValueError(exception_msg)
        if ingress_http:
            http_ingress_conf = await get_http_ingress_values(
                apolo_client,
                ingress_http,
                namespace,
                app_id,
                app_type,
                port_configurations,
            )
        if ingress_grpc:
            grpc_ingress_conf = await get_grpc_ingress_values(
                apolo_client,
                ingress_grpc,
                namespace,
                app_id,
                app_type,
                port_configurations,
            )

        ingress_vals["ingress"] = {
            "enabled": True,  # Enable if either HTTP or gRPC is configured
            **(http_ingress_conf or {}),  # Spread HTTP config if exists
            "grpc": (
                grpc_ingress_conf or {"enabled": False}
            ),  # Add gRPC config under 'grpc' key
        }
        # Ensure annotations dict exists at the top level if http added it,
        # otherwise initialize if only grpc is present.
        if "annotations" not in ingress_vals["ingress"] and grpc_ingress_conf:
            ingress_vals["ingress"]["annotations"] = {}

    app_specific = {}
    if app_id:
        app_specific["apolo_app_id"] = app_id

    return {
        "preset_name": preset_name,
        "resources": resources_vals,
        "tolerations": tolerations_vals,
        "affinity": affinity_vals,
        "podLabels": {
            "platform.apolo.us/component": component_name or "app",
            "platform.apolo.us/preset": preset_name,
        },
        **ingress_vals,
        **app_specific,
    }
