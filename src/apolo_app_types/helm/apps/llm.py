import typing as t

from apolo_sdk import Preset

from apolo_app_types import LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    KEDA_HTTP_PROXY_SERVICE,
    append_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
    get_preset,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common import (
    ApoloFilesMount,
    ApoloMountMode,
    MountPath,
)
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.common.storage import ApoloMountModes


class LLMChartValueProcessor(BaseChartValueProcessor[LLMInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    def _configure_autoscaling(self, input_: LLMInputs) -> dict[str, t.Any]:
        """
        Configure autoscaling.
        """
        if not input_.http_autoscaling:
            return {}
        return {
            "autoscaling": {
                "enabled": True,
                "replicas": {
                    "min": input_.http_autoscaling.min_replicas,
                    "max": input_.http_autoscaling.max_replicas,
                },
                "scaledownPeriod": input_.http_autoscaling.scaledown_period,
                "requestRate": {
                    "granularity": f"{input_.http_autoscaling.request_rate.granularity}"
                    f"s",
                    "targetValue": input_.http_autoscaling.request_rate.target_value,
                    "window": f"{input_.http_autoscaling.request_rate.window_size}s",
                },
                "externalKedaHttpProxyService": KEDA_HTTP_PROXY_SERVICE,
            }
        }

    def _configure_gpu_env(
        self,
        gpu_provider: str,
        gpu_count: int,
    ) -> dict[str, t.Any]:
        """Configure GPU-specific environment variables."""

        device_ids = ",".join(str(i) for i in range(gpu_count))
        gpu_env = {}
        if gpu_provider == "amd":
            gpu_env["envAmd"] = {
                "HIP_VISIBLE_DEVICES": device_ids,
                "ROCR_VISIBLE_DEVICES": device_ids,
            }

        return gpu_env

    def _configure_parallel_args(
        self, server_extra_args: list[str], gpu_count: int
    ) -> list[str]:
        """Configure parallel processing arguments."""
        parallel_server_args: list[str] = []

        has_tensor_parallel = any(
            "tensor-parallel-size" in arg for arg in server_extra_args
        )
        has_pipeline_parallel = any(
            "pipeline-parallel-size" in arg for arg in server_extra_args
        )

        if gpu_count > 1 and not has_tensor_parallel and not has_pipeline_parallel:
            parallel_server_args.append(f"--tensor-parallel-size={gpu_count}")

        return parallel_server_args

    def _configure_model(self, input_: LLMInputs) -> dict[str, str]:
        return {
            "modelHFName": input_.hugging_face_model.model_hf_name,
            "tokenizerHFName": input_.tokenizer_hf_name,
        }

    def _configure_env(
        self, input_: LLMInputs, app_secrets_name: str
    ) -> dict[str, t.Any]:
        # Start with base environment variables
        env_vars = {
            "HUGGING_FACE_HUB_TOKEN": serialize_optional_secret(
                input_.hugging_face_model.hf_token, secret_name=app_secrets_name
            )
        }

        # Add extra environment variables with priority over base ones
        # User-provided extra_env_vars override any existing env vars with the same name
        for env_var in input_.extra_env_vars:
            value = env_var.deserialize_value(app_secrets_name)
            if isinstance(value, str | dict):
                env_vars[env_var.name] = value
            else:
                env_vars[env_var.name] = str(value)

        return env_vars

    def _configure_extra_annotations(self, input_: LLMInputs) -> dict[str, str]:
        extra_annotations: dict[str, str] = {}
        if input_.cache_config:
            storage_mount = ApoloFilesMount(
                storage_uri=input_.cache_config.files_path,
                mount_path=MountPath(path="/root/.cache/huggingface"),
                mode=ApoloMountMode(mode=ApoloMountModes.RW),
            )
            extra_annotations = append_apolo_storage_integration_annotations(
                extra_annotations, [storage_mount], self.client
            )
        return extra_annotations

    def _configure_extra_labels(self, input_: LLMInputs) -> dict[str, str]:
        extra_labels: dict[str, str] = {}
        if input_.cache_config:
            extra_labels.update(
                **gen_apolo_storage_integration_labels(
                    client=self.client, inject_storage=True
                )
            )
        return extra_labels

    def _configure_model_download(self, input_: LLMInputs) -> dict[str, t.Any]:
        if input_.cache_config:
            return {
                "modelDownload": {
                    "hookEnabled": True,
                    "initEnabled": False,
                },
                "cache": {
                    "enabled": False,
                },
            }
        return {
            "modelDownload": {
                "hookEnabled": False,
                "initEnabled": True,
            },
            "cache": {
                "enabled": True,
            },
        }

    async def gen_extra_values(
        self,
        input_: LLMInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for LLM configuration.
        Incorporates:
          - Existing autoscaling logic
          - GPU detection for parallel settings
        """
        app_type = kwargs.get("app_type", AppType.LLMInference)
        values = await gen_extra_values(
            self.client,
            input_.preset,
            app_id,
            app_type,
            input_.ingress_http,
            None,
            namespace,
        )
        values["podAnnotations"] = self._configure_extra_annotations(input_)
        values["podExtraLabels"] = self._configure_extra_labels(input_)
        values.update(self._configure_model_download(input_))

        preset_name = input_.preset.name
        preset: Preset = get_preset(self.client, preset_name)
        nvidia_gpus = preset.nvidia_gpu.count if preset.nvidia_gpu else 0
        amd_gpus = preset.amd_gpu.count if preset.amd_gpu else 0

        gpu_count = nvidia_gpus + amd_gpus
        if amd_gpus > 0:
            gpu_provider = "amd"
        elif nvidia_gpus > 0:
            gpu_provider = "nvidia"
        else:
            gpu_provider = "none"

        values["gpuProvider"] = gpu_provider

        gpu_env = self._configure_gpu_env(gpu_provider, gpu_count)
        parallel_args = self._configure_parallel_args(
            input_.server_extra_args, gpu_count
        )
        server_extra_args = [
            *input_.server_extra_args,
            *parallel_args,
        ]
        model = self._configure_model(input_)
        env = self._configure_env(input_, app_secrets_name)
        autoscaling = self._configure_autoscaling(input_)
        return merge_list_of_dicts(
            [
                {
                    "serverExtraArgs": server_extra_args,
                    "model": model,
                    "llm": model,
                    "env": env,
                },
                gpu_env,
                values,
                autoscaling,
            ]
        )
