from decimal import Decimal
from unittest.mock import patch

import pytest
from apolo_sdk import Preset as ApoloPreset

from apolo_app_types import HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.text_embeddings import (
    _detect_gpu_architecture,
    _get_tei_image_for_architecture,
)
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs

from tests.unit.constants import (
    APP_SECRETS_NAME,
)


@pytest.mark.asyncio
async def test_tei_values_generation(setup_clients):
    # Mock the preset to return CPU-only info
    with patch(
        "apolo_app_types.helm.apps.text_embeddings.get_preset"
    ) as mock_get_preset:

        def return_cpu_preset(_, preset_name):
            return ApoloPreset(
                credits_per_hour=Decimal("1.0"),
                cpu=1.0,
                memory=1024,
                nvidia_gpu=0,  # CPU only
            )

        mock_get_preset.side_effect = return_cpu_preset

        helm_args, helm_params = await app_type_to_vals(
            input_=TextEmbeddingsInferenceAppInputs(
                preset=Preset(name="cpu-small"),
                ingress_http=IngressHttp(
                    clusterName="default",
                ),
                model=HuggingFaceModel(
                    model_hf_name="random/name", hf_token="random-token"
                ),
                server_extra_args=[
                    "--max-concurrent-requests=512",
                    "--max-client-batch-size=16",
                ],
            ),
            apolo_client=setup_clients,
            app_type=AppType.TextEmbeddingsInference,
            app_name="tei-app",
            namespace="default-namespace",
            app_secrets_name=APP_SECRETS_NAME,
        )
        # CPU preset should use CPU image
        assert helm_params["image"] == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "cpu-1.7",
        }
        assert helm_params["model"] == {
            "modelHFName": "random/name",
        }
        assert helm_params["env"] == {
            "HUGGING_FACE_HUB_TOKEN": "random-token",
        }
        assert helm_params["serverExtraArgs"] == [
            "--max-concurrent-requests=512",
            "--max-client-batch-size=16",
        ]


class TestGPUArchitectureDetection:
    """Test GPU architecture detection for dynamic TEI image selection."""

    def test_cpu_preset_no_gpu(self):
        """Test CPU preset with no GPU returns cpu architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"), cpu=1.0, memory=1024, nvidia_gpu=None
        )
        assert _detect_gpu_architecture(preset) == "cpu"

    def test_cpu_preset_zero_gpu(self):
        """Test preset with nvidia_gpu=0 returns cpu architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"), cpu=1.0, memory=1024, nvidia_gpu=0
        )
        assert _detect_gpu_architecture(preset) == "cpu"

    def test_gpu_preset_no_model_defaults_ampere_80(self):
        """Test GPU preset without model info defaults to ampere-80."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=2.0,
            memory=8192,
            nvidia_gpu=1,
            nvidia_gpu_model=None,
        )
        assert _detect_gpu_architecture(preset) == "ampere-80"

    def test_volta_gpu_unsupported_falls_back_cpu(self):
        """Test V100 (Volta) falls back to CPU image."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="Tesla V100",
        )
        assert _detect_gpu_architecture(preset) == "cpu"

    def test_turing_t4_detection(self):
        """Test T4 GPU detected as Turing architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=4.0,
            memory=16384,
            nvidia_gpu=1,
            nvidia_gpu_model="Tesla T4",
        )
        assert _detect_gpu_architecture(preset) == "turing"

    def test_turing_rtx_2080_detection(self):
        """Test RTX 2080 detected as Turing architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=6.0,
            memory=24576,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 2080 Ti",
        )
        assert _detect_gpu_architecture(preset) == "turing"

    def test_ampere_80_a100_detection(self):
        """Test A100 GPU detected as Ampere 80 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A100",
        )
        assert _detect_gpu_architecture(preset) == "ampere-80"

    def test_ampere_80_a30_detection(self):
        """Test A30 GPU detected as Ampere 80 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A30",
        )
        assert _detect_gpu_architecture(preset) == "ampere-80"

    def test_ampere_86_a10_detection(self):
        """Test A10 GPU detected as Ampere 86 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=6.0,
            memory=24576,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A10",
        )
        assert _detect_gpu_architecture(preset) == "ampere-86"

    def test_ampere_86_a40_detection(self):
        """Test A40 GPU detected as Ampere 86 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=12.0,
            memory=49152,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A40",
        )
        assert _detect_gpu_architecture(preset) == "ampere-86"

    def test_ampere_86_rtx_3080_detection(self):
        """Test RTX 3080 detected as Ampere 86 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 3080",
        )
        assert _detect_gpu_architecture(preset) == "ampere-86"

    def test_ada_lovelace_rtx_4090_detection(self):
        """Test RTX 4090 detected as Ada Lovelace architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 4090",
        )
        assert _detect_gpu_architecture(preset) == "ada-lovelace"

    def test_ada_lovelace_rtx_4070_detection(self):
        """Test RTX 4070 detected as Ada Lovelace architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 4070",
        )
        assert _detect_gpu_architecture(preset) == "ada-lovelace"

    def test_hopper_h100_detection(self):
        """Test H100 GPU detected as Hopper architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=32.0,
            memory=131072,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA H100",
        )
        assert _detect_gpu_architecture(preset) == "hopper"

    def test_unknown_gpu_defaults_ampere_80(self):
        """Test unknown GPU model defaults to ampere-80."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=4.0,
            memory=16384,
            nvidia_gpu=1,
            nvidia_gpu_model="Unknown Future GPU",
        )
        assert _detect_gpu_architecture(preset) == "ampere-80"

    def test_case_insensitive_matching(self):
        """Test GPU model matching is case insensitive."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=4.0,
            memory=16384,
            nvidia_gpu=1,
            nvidia_gpu_model="TESLA T4",  # Uppercase
        )
        assert _detect_gpu_architecture(preset) == "turing"


class TestTEIImageSelection:
    """Test TEI Docker image selection based on architecture."""

    def test_cpu_image_selection(self):
        """Test CPU architecture returns CPU image."""
        image_config = _get_tei_image_for_architecture("cpu")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "cpu-1.7",
        }

    def test_turing_image_selection(self):
        """Test Turing architecture returns Turing image."""
        image_config = _get_tei_image_for_architecture("turing")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "turing-1.7",
        }

    def test_ampere_80_image_selection(self):
        """Test Ampere 80 architecture returns default image."""
        image_config = _get_tei_image_for_architecture("ampere-80")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "1.7",
        }

    def test_ampere_86_image_selection(self):
        """Test Ampere 86 architecture returns 86 image."""
        image_config = _get_tei_image_for_architecture("ampere-86")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "86-1.7",
        }

    def test_ada_lovelace_image_selection(self):
        """Test Ada Lovelace architecture returns 89 image."""
        image_config = _get_tei_image_for_architecture("ada-lovelace")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "89-1.7",
        }

    def test_hopper_image_selection(self):
        """Test Hopper architecture returns Hopper image."""
        image_config = _get_tei_image_for_architecture("hopper")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "hopper-1.7",
        }

    def test_unknown_architecture_defaults_ampere_80(self):
        """Test unknown architecture defaults to Ampere 80 image."""
        image_config = _get_tei_image_for_architecture("unknown-arch")
        assert image_config == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "1.7",
        }


@pytest.mark.asyncio
async def test_tei_dynamic_image_selection_a100(setup_clients):
    """Test end-to-end dynamic image selection with A100 GPU."""
    # Mock the preset to return A100 GPU info
    with patch(
        "apolo_app_types.helm.apps.text_embeddings.get_preset"
    ) as mock_get_preset:

        def return_a100_preset(_, preset_name):
            return ApoloPreset(
                credits_per_hour=Decimal("1.0"),
                cpu=16.0,
                memory=65536,
                nvidia_gpu=1,
                nvidia_gpu_model="NVIDIA A100",
            )

        mock_get_preset.side_effect = return_a100_preset

        helm_args, helm_params = await app_type_to_vals(
            input_=TextEmbeddingsInferenceAppInputs(
                preset=Preset(name="a100-large"),
                ingress_http=IngressHttp(clusterName="default"),
                model=HuggingFaceModel(
                    model_hf_name="sentence-transformers/all-MiniLM-L6-v2",
                    hf_token="test-token",
                ),
            ),
            apolo_client=setup_clients,
            app_type=AppType.TextEmbeddingsInference,
            app_name="tei-a100",
            namespace="default-namespace",
            app_secrets_name=APP_SECRETS_NAME,
        )
        # A100 should use the default Ampere 80 image
        assert helm_params["image"] == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "1.7",
        }


@pytest.mark.asyncio
async def test_tei_dynamic_image_selection_t4(setup_clients):
    """Test end-to-end dynamic image selection with T4 GPU."""
    # Mock the preset to return T4 GPU info
    with patch(
        "apolo_app_types.helm.apps.text_embeddings.get_preset"
    ) as mock_get_preset:

        def return_t4_preset(_, preset_name):
            return ApoloPreset(
                credits_per_hour=Decimal("1.0"),
                cpu=4.0,
                memory=16384,
                nvidia_gpu=1,
                nvidia_gpu_model="Tesla T4",
            )

        mock_get_preset.side_effect = return_t4_preset

        helm_args, helm_params = await app_type_to_vals(
            input_=TextEmbeddingsInferenceAppInputs(
                preset=Preset(name="t4-medium"),
                ingress_http=IngressHttp(clusterName="default"),
                model=HuggingFaceModel(
                    model_hf_name="sentence-transformers/all-MiniLM-L6-v2",
                    hf_token="test-token",
                ),
            ),
            apolo_client=setup_clients,
            app_type=AppType.TextEmbeddingsInference,
            app_name="tei-t4",
            namespace="default-namespace",
            app_secrets_name=APP_SECRETS_NAME,
        )
        # T4 should use the Turing experimental image
        assert helm_params["image"] == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "turing-1.7",
        }


@pytest.mark.asyncio
async def test_tei_dynamic_image_selection_cpu(setup_clients):
    """Test end-to-end dynamic image selection with CPU-only preset."""
    # Mock the preset to return CPU-only info
    with patch(
        "apolo_app_types.helm.apps.text_embeddings.get_preset"
    ) as mock_get_preset:

        def return_cpu_preset(_, preset_name):
            return ApoloPreset(
                credits_per_hour=Decimal("1.0"),
                cpu=8.0,
                memory=32768,
                nvidia_gpu=0,  # No GPU
            )

        mock_get_preset.side_effect = return_cpu_preset

        helm_args, helm_params = await app_type_to_vals(
            input_=TextEmbeddingsInferenceAppInputs(
                preset=Preset(name="cpu-large"),
                ingress_http=IngressHttp(clusterName="default"),
                model=HuggingFaceModel(
                    model_hf_name="sentence-transformers/all-MiniLM-L6-v2",
                    hf_token="test-token",
                ),
            ),
            apolo_client=setup_clients,
            app_type=AppType.TextEmbeddingsInference,
            app_name="tei-cpu",
            namespace="default-namespace",
            app_secrets_name=APP_SECRETS_NAME,
        )
        # CPU-only should use the CPU image
        assert helm_params["image"] == {
            "repository": "ghcr.io/huggingface/text-embeddings-inference",
            "tag": "cpu-1.7",
        }
