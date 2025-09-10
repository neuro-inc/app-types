from enum import StrEnum

import pytest

from apolo_app_types.helm.apps.bundles.llm import BaseLLMBundleMixin, ModelSettings
from apolo_app_types.protocols.bundles.llm import LLMBundleInputs
from apolo_app_types.protocols.common import ApoloSecret

from tests.unit.constants import TEST_PRESETS_WITH_EXTRA_LARGE_GPU


class LLMSize(StrEnum):
    size_a = "size_a"
    size_b = "size_b"
    size_c = "size_c"
    size_d = "size_d"
    size_e = "size_e"


class LLMBundleInputs(LLMBundleInputs[LLMSize]):
    llm_class: str = "llm_class"
    size: LLMSize


class StubLLMBundleMixin(BaseLLMBundleMixin[LLMBundleInputs]):
    model_map = {
        LLMSize.size_a: ModelSettings(
            model_hf_name="stub",
            vram_min_required_gb=1,
        ),
        LLMSize.size_b: ModelSettings(
            model_hf_name="stub",
            vram_min_required_gb=10,
        ),
        LLMSize.size_c: ModelSettings(
            model_hf_name="stub",
            vram_min_required_gb=80,
        ),
        LLMSize.size_d: ModelSettings(
            model_hf_name="stub",
            vram_min_required_gb=179,
        ),
        LLMSize.size_e: ModelSettings(
            model_hf_name="stub",
            vram_min_required_gb=1790,
        ),
    }


@pytest.mark.parametrize(
    ("presets_available", "model_size", "expected_preset_name"),
    [
        (TEST_PRESETS_WITH_EXTRA_LARGE_GPU, LLMSize.size_a, "t4-medium"),
        (TEST_PRESETS_WITH_EXTRA_LARGE_GPU, LLMSize.size_b, "t4-medium"),
        (TEST_PRESETS_WITH_EXTRA_LARGE_GPU, LLMSize.size_c, "a100-large"),
        (TEST_PRESETS_WITH_EXTRA_LARGE_GPU, LLMSize.size_d, "gpu-extra-large"),
    ],
    indirect=["presets_available"],
)
async def test_get_preset__ok(
    setup_clients, model_size: LLMSize, expected_preset_name: str, mock_get_preset_gpu
):
    apolo_client = setup_clients
    preset_name = await StubLLMBundleMixin(apolo_client)._get_preset(
        LLMBundleInputs(
            size=model_size,
            hf_token=ApoloSecret(key="FakeSecret"),
        )
    )
    assert preset_name.name == expected_preset_name


@pytest.mark.parametrize(
    "presets_available",
    [TEST_PRESETS_WITH_EXTRA_LARGE_GPU],
    indirect=True,
)
async def test_get_preset__not_enough_vram(setup_clients, mock_get_preset_gpu):
    apolo_client = setup_clients
    with pytest.raises(RuntimeError):
        await StubLLMBundleMixin(apolo_client)._get_preset(
            LLMBundleInputs(
                size=LLMSize.size_e,
                hf_token=ApoloSecret(key="FakeSecret"),
            )
        )
