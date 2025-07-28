import typing as t
from typing import NamedTuple

from apolo_app_types import HuggingFaceModel, LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps import LLMChartValueProcessor
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.utils.text import fuzzy_contains
from apolo_app_types.protocols.bundles.llm import LLama4Inputs, Llama4Size
from apolo_app_types.protocols.common import (
    IngressHttp,
    Preset,
)


class ModelSettings(NamedTuple):
    model_hf_name: str
    gpu_compat: list[str]


class Llama4ValueProcessor(BaseChartValueProcessor[LLama4Inputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        self.llm_val_processor = LLMChartValueProcessor(*args, **kwargs)
        super().__init__(*args, **kwargs)

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    model_map = {
        Llama4Size.scout: ModelSettings(
            model_hf_name="meta-llama/Llama-4-17B-16E", gpu_compat=["a100", "h100"]
        ),
        Llama4Size.scout_instruct: ModelSettings(
            model_hf_name="meta-llama/Llama-4-17B-16E-Instruct",
            gpu_compat=["a100", "h100"],
        ),
        Llama4Size.maverick: ModelSettings(
            model_hf_name="meta-llama/Llama-4-17B-128E", gpu_compat=["a100", "h100"]
        ),
        Llama4Size.maverick_instruct: ModelSettings(
            model_hf_name="meta-llama/Llama-4-17B-128E-Instruct",
            gpu_compat=["a100", "h100"],
        ),
        Llama4Size.maverick_fp8: ModelSettings(
            model_hf_name="meta-llama/Llama-4-17B-128E-Instruct-FP8",
            gpu_compat=["l4", "a100", "h100"],
        ),
    }

    def _get_preset(self, input_: LLama4Inputs) -> Preset:
        """Retrieve the appropriate preset based on the
        input size and GPU compatibility."""
        available_presets = dict(self.client.config.presets)
        model_settings = self.model_map[input_.size]
        compatible_gpus = model_settings.gpu_compat

        for gpu_compat in compatible_gpus:
            for preset_name, _ in available_presets.items():
                if fuzzy_contains(gpu_compat, preset_name, cutoff=0.5):
                    return Preset(name=preset_name)
        # If no preset found, return default
        return Preset(name="default")

    def _llm_inputs(self, input_: LLama4Inputs) -> LLMInputs:
        hf_model = HuggingFaceModel(
            model_hf_name=self.model_map[input_.size].model_hf_name,
            hf_token=input_.hf_token,
        )
        preset_chosen = self._get_preset(input_)
        return LLMInputs(
            hugging_face_model=hf_model,
            tokenizer_hf_name="",
            ingress_http=IngressHttp(),
            preset=preset_chosen,
        )

    async def gen_extra_values(
        self,
        input_: LLama4Inputs,
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
            input_=self._llm_inputs(input_),
            app_name=app_name,
            namespace=namespace,
            app_secrets_name=app_secrets_name,
            app_id=app_id,
            app_type=AppType.Llama4,
        )
