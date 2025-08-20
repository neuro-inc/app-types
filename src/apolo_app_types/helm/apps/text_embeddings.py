import logging
import typing as t

import apolo_sdk

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values, get_preset
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.text_embeddings import (
    TextEmbeddingsInferenceAppInputs,
    TextEmbeddingsInferenceArchitecture,
    TextEmbeddingsInferenceImageTag,
)


logger = logging.getLogger(__name__)

# TEI Docker image repository
TEI_IMAGE_REPOSITORY = "ghcr.io/huggingface/text-embeddings-inference"


def _detect_gpu_architecture(
    preset: apolo_sdk.Preset,
    preset_name: str,
) -> TextEmbeddingsInferenceArchitecture:
    """
    Detect GPU architecture from preset to select appropriate TEI Docker image.

    Returns:
        TextEmbeddingsInferenceArchitecture: Architecture identifier
    """
    # If no NVIDIA GPU, use CPU image
    if not preset.nvidia_gpu:
        # Check for AMD GPU - not supported by TEI, fall back to CPU
        if preset.amd_gpu and preset.amd_gpu.count > 0:
            logger.warning(
                "AMD GPU detected (%s) is not supported by HuggingFace Text "
                "Embeddings Inference. Falling back to CPU image.",
                preset.amd_gpu.model or "Unknown AMD GPU",
            )
        return TextEmbeddingsInferenceArchitecture.CPU

    # Detect architecture based on the preset name, as nvidia_gpu_model may be None.
    preset_name_lowercase = preset_name.lower()
    logger.info(
        "Detecting GPU architecture from preset name: '%s'", preset_name_lowercase
    )

    # Map GPU models to architectures based on HuggingFace TEI documentation
    # Volta (V100) - NOT SUPPORTED by HuggingFace TEI
    if any(
        model in preset_name_lowercase
        for model in ["v100", "volta", "tesla-v100", "tesla-v100-pcie"]
    ):
        logger.warning(
            "GPU model %s (Volta architecture) is not supported by "
            "HuggingFace Text Embeddings Inference. Falling back to CPU image.",
            preset_name,
        )
        return TextEmbeddingsInferenceArchitecture.CPU

    # Turing (T4, RTX 2000 series) - Experimental support
    if any(
        model in preset_name_lowercase
        for model in [
            "t4",
            "rtx 20",
            "rtx20",
            "2080",
            "2070",
            "2060",
            "turing",
            "tesla t4",
        ]
    ):
        return TextEmbeddingsInferenceArchitecture.TURING

    # Ampere 80 (A100, A30)
    if any(
        model in preset_name_lowercase
        for model in ["a100", "a30", "nvidia-a100", "nvidia-a100-sxm4"]
    ):
        return TextEmbeddingsInferenceArchitecture.AMPERE_80

    # Ampere 86 (A10, A40, RTX 3000 series)
    if any(
        model in preset_name_lowercase
        for model in [
            "a10",
            "a10g",
            "a40",
            "rtx 30",
            "rtx30",
            "3090",
            "3080",
            "3070",
            "3060",
            "geforce rtx 30",
        ]
    ):
        return TextEmbeddingsInferenceArchitecture.AMPERE_86

    # Ada Lovelace (RTX 4000 series)
    if any(
        model in preset_name_lowercase
        for model in [
            "l4",
            "nvidia-l4",
            "rtx 40",
            "rtx40",
            "4090",
            "4080",
            "4070",
            "4060",
            "ada",
            "lovelace",
            "geforce rtx 40",
        ]
    ):
        return TextEmbeddingsInferenceArchitecture.ADA_LOVELACE

    # Hopper (H100)
    if any(
        model in preset_name_lowercase
        for model in [
            "h100",
            "hopper",
            "nvidia-h100",
            "nvidia-dgx-h100",
            "nvidia-h100-pcie",
        ]
    ):
        return TextEmbeddingsInferenceArchitecture.HOPPER

    # Unknown GPU model - default to CPU as safest fallback
    logger.warning(
        "Unknown GPU model %s, defaulting to CPU architecture",
        preset_name,
    )
    return TextEmbeddingsInferenceArchitecture.CPU


def _get_tei_image_for_architecture(
    architecture: TextEmbeddingsInferenceArchitecture,
) -> dict[str, str]:
    """
    Get the appropriate HuggingFace Text Embeddings Inference Docker image
    for GPU architecture.

    Args:
        architecture: GPU architecture identifier (enum)

    Returns:
        dict: Image repository and tag configuration
    """
    image_map = {
        TextEmbeddingsInferenceArchitecture.CPU: {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": TextEmbeddingsInferenceImageTag.CPU.value,
        },
        TextEmbeddingsInferenceArchitecture.TURING: {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": TextEmbeddingsInferenceImageTag.TURING.value,
        },
        TextEmbeddingsInferenceArchitecture.AMPERE_80: {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": TextEmbeddingsInferenceImageTag.AMPERE_80.value,
        },
        TextEmbeddingsInferenceArchitecture.AMPERE_86: {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": TextEmbeddingsInferenceImageTag.AMPERE_86.value,
        },
        TextEmbeddingsInferenceArchitecture.ADA_LOVELACE: {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": TextEmbeddingsInferenceImageTag.ADA_LOVELACE.value,
        },
        TextEmbeddingsInferenceArchitecture.HOPPER: {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": TextEmbeddingsInferenceImageTag.HOPPER.value,
        },
    }

    return image_map.get(
        architecture, image_map[TextEmbeddingsInferenceArchitecture.CPU]
    )


class TextEmbeddingsChartValueProcessor(
    BaseChartValueProcessor[TextEmbeddingsInferenceAppInputs]
):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.custom_dep_val_processor = CustomDeploymentChartValueProcessor(
            *args, **kwargs
        )

    def _configure_model_download(
        self, input_: TextEmbeddingsInferenceAppInputs
    ) -> dict[str, t.Any]:
        return {
            "modelHFName": input_.model.model_hf_name,
        }

    def _get_image_params(
        self, input_: TextEmbeddingsInferenceAppInputs
    ) -> dict[str, t.Any]:
        preset_name = input_.preset.name
        # Get the actual preset with GPU information
        apolo_preset = get_preset(self.client, preset_name)

        # Detect GPU architecture and select appropriate image
        architecture = _detect_gpu_architecture(apolo_preset, preset_name)
        image_config = _get_tei_image_for_architecture(architecture)

        logger.info(
            "Selected TEI image for architecture '%s': %s:%s",
            architecture,
            image_config["repository"],
            image_config["tag"],
        )

        return image_config

    def _configure_env(
        self, tei: TextEmbeddingsInferenceAppInputs, app_secrets_name: str
    ) -> dict[str, t.Any]:
        # Start with base environment variables
        env_vars = {
            "HUGGING_FACE_HUB_TOKEN": serialize_optional_secret(
                tei.model.hf_token, secret_name=app_secrets_name
            )
        }

        # Add extra environment variables with priority over base ones
        # User-provided extra_env_vars override any existing env vars with the same name
        for env_var in tei.extra_env_vars:
            value = env_var.deserialize_value(app_secrets_name)
            if isinstance(value, str | dict):
                env_vars[env_var.name] = value
            else:
                env_vars[env_var.name] = str(value)

        return env_vars

    async def gen_extra_values(
        self,
        input_: TextEmbeddingsInferenceAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for TEI configuration.
        """
        values = await gen_extra_values(
            self.client,
            input_.preset,
            app_id,
            AppType.TextEmbeddingsInference,
            input_.ingress_http,
            None,
            namespace,
        )
        model = self._configure_model_download(input_)
        image = self._get_image_params(input_)
        env = self._configure_env(input_, app_secrets_name)
        return merge_list_of_dicts(
            [
                {
                    "model": model,
                    "image": image,
                    "env": env,
                    "serverExtraArgs": input_.server_extra_args,
                },
                values,
            ]
        )
