import logging
import typing as t
from decimal import Decimal
from typing import NamedTuple

from apolo_app_types import HuggingFaceModel, LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps import LLMChartValueProcessor
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.protocols.bundles.llm import (
    DeepSeekR1Inputs,
    DeepSeekR1Size,
    GptOssSize,
    LLama4Inputs,
    Llama4Size,
    MistralInputs,
    MistralSize,
)
from apolo_app_types.protocols.common import (
    ApoloFilesPath,
    HuggingFaceCache,
    IngressHttp,
    Preset,
)
from apolo_app_types.protocols.common.autoscaling import AutoscalingKedaHTTP


class ModelSettings(NamedTuple):
    model_hf_name: str
    vram_min_required_gb: float


T = t.TypeVar("T", LLama4Inputs, DeepSeekR1Inputs, MistralInputs)


logger = logging.getLogger(__name__)


class BaseLLMBundleMixin(BaseChartValueProcessor[T]):
    """
    Base class for LLM bundle value processors.
    This class provides common functionality for processing LLM inputs
    and generating extra values for LLM applications.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        self.llm_val_processor = LLMChartValueProcessor(*args, **kwargs)
        super().__init__(*args, **kwargs)

    cache_prefix: str = "llm_bundles"
    model_map: dict[str, ModelSettings]
    app_type: AppType

    def _get_storage_path(self) -> str:
        """
        Returns the storage path for the LLM inputs.
        :param input_:
        :return:
        """
        cluster_name = self.client.config.cluster_name
        project_name = self.client.config.project_name
        org_name = self.client.config.org_name
        return f"storage://{cluster_name}/{org_name}/{project_name}/{self.cache_prefix}"

    async def _get_preset(
        self,
        input_: T,
    ) -> Preset:
        """Retrieve the appropriate preset based on the
        input size and GPU compatibility."""
        available_presets = dict(self.client.config.presets)
        jobs_capacity = await self.client.jobs.get_capacity()
        model_settings = self.model_map[input_.size]
        min_total_vram_gb = model_settings.vram_min_required_gb

        candidates: list[tuple[Decimal, int, float, int, str]] = []
        for preset_name, available_preset in available_presets.items():
            gpu = available_preset.nvidia_gpu or available_preset.amd_gpu
            if not gpu:
                msg = f"Ignoring preset {preset_name} because it has no GPU"
                logger.info(msg)
                continue

            instances_capacity = jobs_capacity.get(preset_name, 0)
            if instances_capacity <= 0:
                msg = f"Ignoring preset {preset_name} because it has no capacity"
                logger.info(msg)
                continue

            mem_bytes = gpu.memory or 0
            cnt = gpu.count
            if mem_bytes <= 0 or cnt <= 0:
                msg = f"Ignoring preset {preset_name} because its GPU memory is <= 0"
                logger.info(msg)
                continue

            mem_gb = mem_bytes / 1e9
            total_vram = float(mem_gb) * int(cnt)
            if not total_vram >= min_total_vram_gb:
                msg = f"Preset {preset_name} has not enough VRAM"
                logger.info(msg)
                continue
                # in most of the cases, credits price will be different for each preset
            candidates.append(
                (
                    available_preset.credits_per_hour,
                    -instances_capacity,
                    total_vram,
                    cnt,
                    preset_name,
                )
            )

        if not candidates:
            err_msg = (
                f"No preset satisfies total VRAM ≥ "
                f"{min_total_vram_gb} for size={input_.size!r}."
            )
            raise RuntimeError(err_msg)
        logger.info("Candidates: %s", candidates)
        # Prefer smallest total VRAM
        best_name = min(candidates)[-1]
        return Preset(name=best_name)

    async def _llm_inputs(self, input_: T) -> LLMInputs:
        hf_model = HuggingFaceModel(
            model_hf_name=self.model_map[input_.size].model_hf_name,
            hf_token=input_.hf_token,
        )
        preset_chosen = await self._get_preset(input_)
        logger.info("Preset chosen: %s", preset_chosen.name)
        return LLMInputs(
            hugging_face_model=hf_model,
            tokenizer_hf_name=hf_model.model_hf_name,
            ingress_http=IngressHttp(auth=False),
            preset=preset_chosen,
            cache_config=HuggingFaceCache(
                files_path=ApoloFilesPath(path=self._get_storage_path())
            ),
            http_autoscaling=AutoscalingKedaHTTP(scaledown_period=300)
            if input_.autoscaling_enabled
            else None,
        )

    async def gen_extra_values(
        self,
        input_: T,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generates additional key-value pairs for use in application-specific processing
        based on the provided input and other parameters. This method executes in an
        asynchronous manner, allowing for non-blocking operations.

        :param input_: An instance of LLamaInputs containing the input data required
                       for processing.
        :param app_name: The name of the application for which the extra values
                         are being generated.
        :param namespace: The namespace associated with the application.
        :param app_id: The identifier of the application.
        :param app_secrets_name: The name of the application's secret store or
                                 credentials configuration.
        :param _: Additional positional arguments.
        :param kwargs: Additional keyword arguments for further customization or
                       processing.
        :return: A dictionary containing the generated key-value pairs as extra
                 values for the specified application.
        """

        return await self.llm_val_processor.gen_extra_values(
            input_=await self._llm_inputs(input_),
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
            app_id=app_id,
            app_type=self.app_type,
        )

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]


class Llama4ValueProcessor(BaseLLMBundleMixin[LLama4Inputs]):
    app_type = AppType.Llama4
    model_map = {
        Llama4Size.scout: ModelSettings(
            model_hf_name="meta-llama/Llama-4-Scout-17B-16E",
            vram_min_required_gb=80,
        ),
        Llama4Size.scout_instruct: ModelSettings(
            model_hf_name="meta-llama/Llama-4-Scout-17B-16E-Instruct",
            vram_min_required_gb=80,
        ),
    }


class DeepSeekValueProcessor(BaseLLMBundleMixin[DeepSeekR1Inputs]):
    app_type = AppType.DeepSeek
    model_map = {
        DeepSeekR1Size.r1: ModelSettings(
            model_hf_name="deepseek-ai/DeepSeek-R1", vram_min_required_gb=1342.0
        ),
        DeepSeekR1Size.r1_zero: ModelSettings(
            model_hf_name="deepseek-ai/DeepSeek-R1-Zero", vram_min_required_gb=1342.0
        ),
        DeepSeekR1Size.r1_distill_llama_8b: ModelSettings(
            model_hf_name="deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
            vram_min_required_gb=18.0,
        ),
        DeepSeekR1Size.r1_distill_llama_70b: ModelSettings(
            model_hf_name="deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            vram_min_required_gb=161.0,
        ),
        DeepSeekR1Size.r1_distill_qwen_1_5_b: ModelSettings(
            model_hf_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            vram_min_required_gb=3.9,
        ),
    }


class MistralValueProcessor(BaseLLMBundleMixin[MistralInputs]):
    app_type = AppType.Mistral
    model_map = {
        MistralSize.mistral_7b_v02: ModelSettings(
            model_hf_name="mistralai/Mistral-7B-Instruct-v0.2",
            vram_min_required_gb=5,
        ),
        MistralSize.mistral_7b_v03: ModelSettings(
            model_hf_name="mistralai/Mistral-7B-Instruct-v0.3",
            vram_min_required_gb=5,
        ),
        MistralSize.mistral_31_24b_instruct: ModelSettings(
            model_hf_name="mistralai/Mistral-Small-3.1-24B-Instruct-2503",
            vram_min_required_gb=16,
        ),
        MistralSize.mistral_32_24b_instruct: ModelSettings(
            model_hf_name="mistralai/Mistral-Small-3.2-24B-Instruct-2506",
            vram_min_required_gb=16,
        ),
    }


class GPTOSSValueProcessor(BaseLLMBundleMixin[MistralInputs]):
    app_type = AppType.GptOss
    model_map = {
        GptOssSize.gpt_oss_20b: ModelSettings(
            model_hf_name="openai/gpt-oss-20b",
            vram_min_required_gb=16.0,
        ),
        GptOssSize.gpt_oss_120b: ModelSettings(
            model_hf_name="openai/gpt-oss-120b",
            vram_min_required_gb=80.0,
        ),
    }
