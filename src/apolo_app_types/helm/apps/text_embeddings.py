import logging
import typing as t

import apolo_sdk

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values, get_preset
from apolo_app_types.helm.apps.custom_deployment import (
    CustomDeploymentChartValueProcessor,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs


logger = logging.getLogger(__name__)


def _detect_gpu_architecture(preset: apolo_sdk.Preset) -> str:
    """
    Detect GPU architecture from preset to select appropriate TEI Docker image.

    Returns:
        str: Architecture identifier (cpu, turing, ampere-80, ampere-86,
             ada-lovelace, hopper)
    """
    # If no NVIDIA GPU, use CPU image
    if not preset.nvidia_gpu or preset.nvidia_gpu == 0:
        return "cpu"

    # If no GPU model specified, default to ampere-80 (safest choice)
    if not preset.nvidia_gpu_model:
        logger.warning(
            "No GPU model specified in preset, defaulting to ampere-80 architecture"
        )
        return "ampere-80"

    gpu_model = preset.nvidia_gpu_model.lower()

    # Map GPU models to architectures based on HuggingFace TEI documentation
    # Volta (V100) - NOT SUPPORTED by HuggingFace TEI
    if any(model in gpu_model for model in ["v100", "volta"]):
        logger.warning(
            "GPU model %s (Volta architecture) is not supported by "
            "HuggingFace Text Embeddings Inference. Falling back to CPU image.",
            preset.nvidia_gpu_model,
        )
        return "cpu"

    # Turing (T4, RTX 2000 series) - Experimental support
    if any(
        model in gpu_model
        for model in ["t4", "rtx 20", "rtx20", "2080", "2070", "2060"]
    ):
        return "turing"

    # Ampere 80 (A100, A30)
    if any(model in gpu_model for model in ["a100", "a30"]):
        return "ampere-80"

    # Ampere 86 (A10, A40, RTX 3000 series)
    if any(
        model in gpu_model
        for model in ["a10", "a40", "rtx 30", "rtx30", "3090", "3080", "3070", "3060"]
    ):
        return "ampere-86"

    # Ada Lovelace (RTX 4000 series)
    if any(
        model in gpu_model
        for model in ["rtx 40", "rtx40", "4090", "4080", "4070", "4060", "ada"]
    ):
        return "ada-lovelace"

    # Hopper (H100)
    if any(model in gpu_model for model in ["h100", "hopper"]):
        return "hopper"

    # Unknown GPU model - default to ampere-80 as safest fallback
    logger.warning(
        "Unknown GPU model %s, defaulting to ampere-80 architecture",
        preset.nvidia_gpu_model,
    )
    return "ampere-80"


def _get_tei_image_for_architecture(architecture: str) -> dict[str, str]:
    """
    Get the appropriate HuggingFace Text Embeddings Inference Docker image
    for GPU architecture.

    Args:
        architecture: GPU architecture identifier

    Returns:
        dict: Image repository and tag configuration
    """
    image_map = {
        "cpu": {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "cpu-1.7",
        },
        "turing": {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "turing-1.7",
        },
        "ampere-80": {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "1.7",  # Default/main image for A100/A30
        },
        "ampere-86": {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "86-1.7",
        },
        "ada-lovelace": {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "89-1.7",
        },
        "hopper": {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "hopper-1.7",
        },
    }

    return image_map.get(architecture, image_map["ampere-80"])


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
        # Get the actual preset with GPU information
        apolo_preset = get_preset(self.client, input_.preset.name)

        # Detect GPU architecture and select appropriate image
        architecture = _detect_gpu_architecture(apolo_preset)
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
