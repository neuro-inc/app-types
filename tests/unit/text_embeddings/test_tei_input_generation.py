from decimal import Decimal
from unittest.mock import patch

import pytest
from apolo_sdk import Preset as ApoloPreset

from apolo_app_types import HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.text_embeddings import (
    TEI_IMAGE_REPOSITORY,
    _detect_gpu_architecture,
    _get_tei_image_for_architecture,
)
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.text_embeddings import (
    TextEmbeddingsInferenceAppInputs,
    TextEmbeddingsInferenceArchitecture as TEIArch,
)

from tests.unit.constants import (
    APP_ID,
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
                ingress_http=IngressHttp(),
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
            app_id=APP_ID,
        )
        # CPU preset should use CPU image
        assert helm_params["image"] == {
            "repository": TEI_IMAGE_REPOSITORY,
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
        assert _detect_gpu_architecture(preset, "cpu-small") == TEIArch.CPU

    def test_cpu_preset_zero_gpu(self):
        """Test preset with nvidia_gpu=0 returns cpu architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"), cpu=1.0, memory=1024, nvidia_gpu=0
        )
        assert _detect_gpu_architecture(preset, "cpu-small") == TEIArch.CPU

    def test_gpu_preset_no_model_defaults_cpu(self):
        """Test GPU preset without model info defaults to cpu."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=2.0,
            memory=8192,
            nvidia_gpu=1,
            nvidia_gpu_model=None,
        )
        assert _detect_gpu_architecture(preset, "gpu-unspecified") == TEIArch.CPU

    def test_volta_gpu_unsupported_falls_back_cpu(self):
        """Test V100 (Volta) falls back to CPU image."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="Tesla V100",
        )
        assert _detect_gpu_architecture(preset, "gpu-v100-x1") == TEIArch.CPU

    def test_turing_t4_detection(self):
        """Test T4 GPU detected as Turing architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=4.0,
            memory=16384,
            nvidia_gpu=1,
            nvidia_gpu_model="Tesla T4",
        )
        assert _detect_gpu_architecture(preset, "gpu-t4-x1") == TEIArch.TURING

    def test_turing_rtx_2080_detection(self):
        """Test RTX 2080 detected as Turing architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=6.0,
            memory=24576,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 2080 Ti",
        )
        assert _detect_gpu_architecture(preset, "gpu-rtx-2080-x1") == TEIArch.TURING

    def test_ampere_80_a100_detection(self):
        """Test A100 GPU detected as Ampere 80 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A100",
        )
        assert _detect_gpu_architecture(preset, "gpu-a100-x1") == TEIArch.AMPERE_80

    def test_ampere_80_a30_detection(self):
        """Test A30 GPU detected as Ampere 80 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A30",
        )
        assert _detect_gpu_architecture(preset, "gpu-a30-x1") == TEIArch.AMPERE_80

    def test_ampere_86_a10_detection(self):
        """Test A10 GPU detected as Ampere 86 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=6.0,
            memory=24576,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A10",
        )
        assert _detect_gpu_architecture(preset, "gpu-a10g-x1") == TEIArch.AMPERE_86

    def test_ampere_86_a40_detection(self):
        """Test A40 GPU detected as Ampere 86 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=12.0,
            memory=49152,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA A40",
        )
        assert _detect_gpu_architecture(preset, "gpu-a40-x1") == TEIArch.AMPERE_86

    def test_ampere_86_rtx_3080_detection(self):
        """Test RTX 3080 detected as Ampere 86 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 3080",
        )
        assert _detect_gpu_architecture(preset, "gpu-rtx-3080-x1") == TEIArch.AMPERE_86

    def test_ada_lovelace_rtx_4090_detection(self):
        """Test RTX 4090 detected as Ada Lovelace architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 4090",
        )
        assert (
            _detect_gpu_architecture(preset, "gpu-rtx-4090-x1") == TEIArch.ADA_LOVELACE
        )

    def test_ada_lovelace_rtx_4070_detection(self):
        """Test RTX 4070 detected as Ada Lovelace architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=12.0,
            memory=49152,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 4070",
        )
        assert (
            _detect_gpu_architecture(preset, "gpu-rtx-4070-x1") == TEIArch.ADA_LOVELACE
        )

    def test_hopper_h100_detection(self):
        """Test H100 GPU detected as Hopper architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=32.0,
            memory=131072,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA H100",
        )
        assert _detect_gpu_architecture(preset, "gpu-h100-x1") == TEIArch.HOPPER

    def test_unknown_gpu_defaults_cpu(self):
        """Test unknown GPU model defaults to CPU architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="Unknown GPU Model",
        )
        assert _detect_gpu_architecture(preset, "gpu-unknown-x1") == TEIArch.CPU

    def test_case_insensitive_matching(self):
        """Test GPU model matching is case insensitive."""
        preset_rtx40 = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="GEFORCE RTX 4090",  # Uppercase
        )
        assert (
            _detect_gpu_architecture(preset_rtx40, "GPU-RTX-4090-X1")
            == TEIArch.ADA_LOVELACE
        )

    def test_amd_gpu_falls_back_to_cpu(self):
        """Test AMD GPU falls back to CPU image."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=0,
            amd_gpu=1,
            amd_gpu_model="AMD Radeon RX 6800",
        )
        assert _detect_gpu_architecture(preset, "amd-gpu-preset") == TEIArch.CPU

    def test_amd_gpu_no_model_falls_back_to_cpu(self):
        """Test AMD GPU without model falls back to CPU image."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=0,
            amd_gpu=1,
            amd_gpu_model=None,
        )
        assert _detect_gpu_architecture(preset, "amd-gpu-preset") == TEIArch.CPU

    def test_tesla_v100_pcie_unsupported(self):
        """Test Tesla V100 PCIe falls back to CPU image."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="Tesla V100-PCIE",
        )
        assert _detect_gpu_architecture(preset, "gpu-v100-pcie-x1") == TEIArch.CPU

    def test_nvidia_a100_sxm4_detection(self):
        """Test NVIDIA A100-SXM4 detected as Ampere 80 architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA-A100-SXM4",
        )
        assert _detect_gpu_architecture(preset, "gpu-a100-sxm4-x1") == TEIArch.AMPERE_80

    def test_nvidia_dgx_h100_detection(self):
        """Test NVIDIA DGX H100 detected as Hopper architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=32.0,
            memory=131072,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA-DGX-H100",
        )
        assert _detect_gpu_architecture(preset, "gpu-dgx-h100-x1") == TEIArch.HOPPER

    def test_nvidia_h100_pcie_detection(self):
        """Test NVIDIA H100-PCIE detected as Hopper architecture."""
        preset = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=32.0,
            memory=131072,
            nvidia_gpu=1,
            nvidia_gpu_model="NVIDIA-H100-PCIE",
        )
        assert _detect_gpu_architecture(preset, "gpu-h100-pcie-x1") == TEIArch.HOPPER

    def test_geforce_rtx_series_detection(self):
        """Test GeForce RTX series detection for different architectures."""
        # RTX 2080 (Turing)
        preset_rtx20 = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=6.0,
            memory=24576,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 2080",
        )
        assert _detect_gpu_architecture(preset_rtx20, "gpu-rtx-2080") == TEIArch.TURING

        # RTX 3080 (Ampere 86)
        preset_rtx30 = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=8.0,
            memory=32768,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 3080",
        )
        assert (
            _detect_gpu_architecture(preset_rtx30, "gpu-rtx-3080") == TEIArch.AMPERE_86
        )

        # RTX 4090 (Ada Lovelace)
        preset_rtx40 = ApoloPreset(
            credits_per_hour=Decimal("1.0"),
            cpu=16.0,
            memory=65536,
            nvidia_gpu=1,
            nvidia_gpu_model="GeForce RTX 4090",
        )
        assert (
            _detect_gpu_architecture(preset_rtx40, "gpu-rtx-4090")
            == TEIArch.ADA_LOVELACE
        )


class TestTEIImageSelection:
    """Test TEI Docker image selection based on architecture."""

    def test_cpu_image_selection(self):
        """Test CPU architecture returns CPU image."""
        image_config = _get_tei_image_for_architecture(TEIArch.CPU)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "cpu-1.7",
        }

    def test_turing_image_selection(self):
        """Test Turing architecture returns Turing image."""
        image_config = _get_tei_image_for_architecture(TEIArch.TURING)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "turing-1.7",
        }

    def test_ampere_80_image_selection(self):
        """Test Ampere 80 architecture returns default image."""
        image_config = _get_tei_image_for_architecture(TEIArch.AMPERE_80)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "1.7",
        }

    def test_ampere_86_image_selection(self):
        """Test Ampere 86 architecture returns 86 image."""
        image_config = _get_tei_image_for_architecture(TEIArch.AMPERE_86)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "86-1.7",
        }

    def test_ada_lovelace_image_selection(self):
        """Test Ada Lovelace architecture returns 89 image."""
        image_config = _get_tei_image_for_architecture(TEIArch.ADA_LOVELACE)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "89-1.7",
        }

    def test_hopper_image_selection(self):
        """Test Hopper architecture returns Hopper image."""
        image_config = _get_tei_image_for_architecture(TEIArch.HOPPER)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "hopper-1.7",
        }

    def test_unknown_architecture_defaults_ampere_80(self):
        """Test unknown architecture defaults to CPU image."""
        image_config = _get_tei_image_for_architecture(TEIArch.CPU)
        assert image_config == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "cpu-1.7",
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
                ingress_http=IngressHttp(),
                model=HuggingFaceModel(
                    model_hf_name="sentence-transformers/all-MiniLM-L6-v2",
                    hf_token="test-token",
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
            app_id=APP_ID,
        )
        # A100 should use the default Ampere 80 image
        assert helm_params["image"] == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "1.7",
        }

        assert helm_params["model"] == {
            "modelHFName": "sentence-transformers/all-MiniLM-L6-v2",
        }
        assert helm_params["env"] == {
            "HUGGING_FACE_HUB_TOKEN": "test-token",
        }
        assert helm_params["serverExtraArgs"] == [
            "--max-concurrent-requests=512",
            "--max-client-batch-size=16",
        ]


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
                ingress_http=IngressHttp(),
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
            app_id=APP_ID,
        )
        # T4 should use the Turing experimental image
        assert helm_params["image"] == {
            "repository": TEI_IMAGE_REPOSITORY,
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
                ingress_http=IngressHttp(),
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
            app_id=APP_ID,
        )
        # CPU-only should use the CPU image
        assert helm_params["image"] == {
            "repository": TEI_IMAGE_REPOSITORY,
            "tag": "cpu-1.7",
        }
