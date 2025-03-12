import typing as t

from apolo_sdk import Preset

from apolo_app_types import LLMInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    gen_apolo_storage_integration_annotations,
    gen_apolo_storage_integration_labels,
    gen_extra_values,
    get_preset,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common import (
    ApoloMountMode,
    ApoloStorageMount,
    MountPath,
)
from apolo_app_types.protocols.common.hugging_face import serialize_hf_token
from apolo_app_types.protocols.llm import LLMModel


class LLMChartValueProcessor(BaseChartValueProcessor[LLMInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

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
        elif gpu_provider == "nvidia":
            gpu_env["envNvidia"] = {"CUDA_VISIBLE_DEVICES": device_ids}

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

    def _configure_model(self, llm_model: LLMModel) -> dict[str, str]:
        return {
            "modelHFName": llm_model.hugging_face_model.modelHFName,
            "tokenizerHFName": llm_model.tokenizerHFName,
        }

    def _configure_env(self, llm_model: LLMModel) -> dict[str, t.Any]:
        return {
            "HUGGING_FACE_HUB_TOKEN": serialize_hf_token(
                llm_model.hugging_face_model.hfToken
            )
        }

    def _configure_extra_annotations(self, input_: LLMInputs) -> dict[str, str]:
        extra_annotations: dict[str, str] = {}
        if input_.storage_cache:
            storage_mount = ApoloStorageMount(
                storage_path=input_.storage_cache.storage_cache.storage_path,
                mount_path=MountPath(path="/root/.cache/huggingface"),
                mode=ApoloMountMode(mode="rw"),
            )
            extra_annotations.update(
                **gen_apolo_storage_integration_annotations([storage_mount])
            )
        return extra_annotations

    def _configure_extra_labels(self, input_: LLMInputs) -> dict[str, str]:
        extra_labels: dict[str, str] = {}
        if input_.storage_cache:
            extra_labels.update(
                **gen_apolo_storage_integration_labels(inject_storage=True)
            )
        return extra_labels

    def _configure_model_download(self, input_: LLMInputs) -> dict[str, t.Any]:
        if input_.storage_cache:
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
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for LLM configuration.
        Incorporates:
          - Existing autoscaling logic
          - GPU detection for parallel settings
        """
        values = await gen_extra_values(
            self.client,
            input_.preset,
            input_.ingress,
            namespace,
        )
        values["podAnnotations"] = self._configure_extra_annotations(input_)
        values["podExtraLabels"] = self._configure_extra_labels(input_)
        values.update(self._configure_model_download(input_))

        preset_name = input_.preset.name
        preset: Preset = get_preset(self.client, preset_name)
        nvidia_gpus = preset.nvidia_gpu or 0
        amd_gpus = preset.amd_gpu or 0

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
            input_.llm.serverExtraArgs, gpu_count
        )
        server_extra_args = [
            *input_.llm.serverExtraArgs,
            *parallel_args,
        ]
        model = self._configure_model(input_.llm)
        env = self._configure_env(input_.llm)
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
            ]
        )
