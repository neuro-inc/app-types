import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.common.storage import ApoloFilesPath
from apolo_app_types.protocols.launchpad import (
    AppsConfig,
    CustomLLMModel,
    HuggingFaceLLMModel,
    LaunchpadAppInputs,
    LaunchpadConfig,
    LLMConfig,
    PreConfiguredLLMModels,
)

from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
)


@pytest.mark.asyncio
async def test_launchpad_values_generation_with_preconfigured_model(setup_clients):
    """Test launchpad helm values generation with a pre-configured LLM model."""
    helm_args, helm_params = await app_type_to_vals(
        input_=LaunchpadAppInputs(
            launchpad_config=LaunchpadConfig(
                preset=Preset(name="cpu-small"),
            ),
            apps_config=AppsConfig(
                llm_config=LLMConfig(
                    llm_model=PreConfiguredLLMModels.LLAMA_31_8b,
                    llm_preset=Preset(name="gpu-small"),
                    ui_preset=Preset(name="cpu-small"),
                )
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Launchpad,
        app_name="launchpad-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    # Basic helm parameter structure
    assert "LAUNCHPAD_INITIAL_CONFIG" in helm_params
    config = helm_params["LAUNCHPAD_INITIAL_CONFIG"]

    assert config["llm_config"]["llm_model"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert config["llm_config"]["llm_preset"]["name"] == "gpu-small"
    assert config["llm_config"]["ui_preset"]["name"] == "cpu-small"


@pytest.mark.asyncio
async def test_launchpad_values_generation_with_huggingface_model(setup_clients):
    """Test launchpad helm values generation with a HuggingFace LLM model."""
    from apolo_app_types import Env, HuggingFaceModel

    helm_args, helm_params = await app_type_to_vals(
        input_=LaunchpadAppInputs(
            launchpad_config=LaunchpadConfig(
                preset=Preset(name="cpu-small"),
            ),
            apps_config=AppsConfig(
                llm_config=LLMConfig(
                    llm_model=HuggingFaceLLMModel(
                        llm_model=HuggingFaceModel(
                            model_hf_name="microsoft/DialoGPT-medium",
                        ),
                        vllm_extra_args=[
                            Env(name="MAX_MODEL_LEN", value="2048"),
                            Env(name="GPU_MEMORY_UTILIZATION", value="0.9"),
                        ],
                    ),
                    llm_preset=Preset(name="gpu-large"),
                    ui_preset=Preset(name="cpu-medium"),
                )
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Launchpad,
        app_name="launchpad-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    config = helm_params["LAUNCHPAD_INITIAL_CONFIG"]

    # Check HuggingFace model configuration
    llm_model_config = config["llm_config"]["llm_model"]
    assert llm_model_config["llm_model"]["model_hf_name"] == "microsoft/DialoGPT-medium"

    # Check VLLM extra args
    vllm_args = llm_model_config["vllm_extra_args"]
    assert len(vllm_args) == 2
    assert vllm_args[0]["name"] == "MAX_MODEL_LEN"
    assert vllm_args[0]["value"] == "2048"
    assert vllm_args[1]["name"] == "GPU_MEMORY_UTILIZATION"
    assert vllm_args[1]["value"] == "0.9"

    # Check presets
    assert config["llm_config"]["llm_preset"]["name"] == "gpu-large"
    assert config["llm_config"]["ui_preset"]["name"] == "cpu-medium"


@pytest.mark.asyncio
async def test_launchpad_values_generation_with_custom_model(setup_clients):
    """Test launchpad helm values generation with a custom LLM model."""
    helm_args, helm_params = await app_type_to_vals(
        input_=LaunchpadAppInputs(
            launchpad_config=LaunchpadConfig(
                preset=Preset(name="cpu-small"),
            ),
            apps_config=AppsConfig(
                llm_config=LLMConfig(
                    llm_model=CustomLLMModel(
                        llm_model_name="my-custom-model",
                        llm_model_apolo_path=ApoloFilesPath(
                            path="storage://cluster/org/project/models/my-model"
                        ),
                        vllm_extra_args=[
                            "--max-model-len",
                            "4096",
                            "--tensor-parallel-size",
                            "2",
                        ],
                    ),
                    llm_preset=Preset(name="gpu-xlarge"),
                    ui_preset=Preset(name="cpu-small"),
                )
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Launchpad,
        app_name="launchpad-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    config = helm_params["LAUNCHPAD_INITIAL_CONFIG"]

    # Check custom model configuration
    llm_model_config = config["llm_config"]["llm_model"]
    assert llm_model_config["llm_model_name"] == "my-custom-model"
    assert (
        llm_model_config["llm_model_apolo_path"]["path"]
        == "storage://cluster/org/project/models/my-model"
    )

    # Check VLLM extra args
    vllm_args = llm_model_config["vllm_extra_args"]
    assert vllm_args == ["--max-model-len", "4096", "--tensor-parallel-size", "2"]

    # Check presets
    assert config["llm_config"]["llm_preset"]["name"] == "gpu-xlarge"
    assert config["llm_config"]["ui_preset"]["name"] == "cpu-small"


@pytest.mark.asyncio
async def test_launchpad_values_generation_magistral_model(setup_clients):
    """Test launchpad helm values generation with Magistral pre-configured model."""
    helm_args, helm_params = await app_type_to_vals(
        input_=LaunchpadAppInputs(
            launchpad_config=LaunchpadConfig(
                preset=Preset(name="cpu-medium"),
            ),
            apps_config=AppsConfig(
                llm_config=LLMConfig(
                    llm_model=PreConfiguredLLMModels.MAGISTRAL_24B,
                    llm_preset=Preset(name="gpu-medium"),
                    ui_preset=Preset(name="cpu-small"),
                )
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Launchpad,
        app_name="launchpad-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    config = helm_params["LAUNCHPAD_INITIAL_CONFIG"]

    assert config["llm_config"]["llm_model"] == "unsloth/Magistral-Small-2506-GGUF"
    assert config["llm_config"]["llm_preset"]["name"] == "gpu-medium"
    assert config["llm_config"]["ui_preset"]["name"] == "cpu-small"
