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
    PostgresConfig,
    PreConfiguredEmbeddingsModels,
    PreConfiguredLLMModels,
    TextEmbeddingsConfig,
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
                    model=PreConfiguredLLMModels.LLAMA_31_8b,
                    llm_preset=Preset(name="gpu-small"),
                    ui_preset=Preset(name="cpu-small"),
                ),
                postgres_config=PostgresConfig(
                    preset=Preset(name="cpu-small"),
                ),
                embeddings_config=TextEmbeddingsConfig(
                    model=PreConfiguredEmbeddingsModels.BAAI_BGE_M3,
                    preset=Preset(name="gpu-small"),
                ),
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

    assert (
        config["vllm"]["hugging_face_model"]["model_hf_name"]
        == "meta-llama/Llama-3.1-8B-Instruct"
    )
    assert config["vllm"]["preset"]["name"] == "gpu-small"


@pytest.mark.asyncio
async def test_launchpad_values_generation_with_huggingface_model(setup_clients):
    """Test launchpad helm values generation with a HuggingFace LLM model."""
    from apolo_app_types import HuggingFaceModel

    helm_args, helm_params = await app_type_to_vals(
        input_=LaunchpadAppInputs(
            launchpad_config=LaunchpadConfig(
                preset=Preset(name="cpu-small"),
            ),
            apps_config=AppsConfig(
                llm_config=LLMConfig(
                    model=HuggingFaceLLMModel(
                        hf_model=HuggingFaceModel(
                            model_hf_name="microsoft/DialoGPT-medium",
                        ),
                        server_extra_args=[
                            "--max-model-len=2048",
                            "--gpu-memory-utilization=0.9",
                        ],
                    ),
                    llm_preset=Preset(name="gpu-large"),
                    ui_preset=Preset(name="cpu-medium"),
                ),
                postgres_config=PostgresConfig(
                    preset=Preset(name="cpu-small"),
                ),
                embeddings_config=TextEmbeddingsConfig(
                    model=PreConfiguredEmbeddingsModels.BAAI_BGE_M3,
                    preset=Preset(name="gpu-small"),
                ),
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
    llm_model_config = config["vllm"]
    assert (
        llm_model_config["hugging_face_model"]["model_hf_name"]
        == "microsoft/DialoGPT-medium"
    )

    # Check VLLM extra args
    vllm_args = llm_model_config["server_extra_args"]
    assert len(vllm_args) == 2
    assert vllm_args[0] == "--max-model-len=2048"
    assert vllm_args[1] == "--gpu-memory-utilization=0.9"

    # Check presets
    assert config["vllm"]["preset"]["name"] == "gpu-large"


@pytest.mark.asyncio
async def test_launchpad_values_generation_with_custom_model(setup_clients):
    """Test launchpad helm values generation with a custom LLM model."""
    # Custom models are not yet supported, so this should raise a ValueError
    with pytest.raises(ValueError, match="Unsupported LLM model type"):
        helm_args, helm_params = await app_type_to_vals(
            input_=LaunchpadAppInputs(
                launchpad_config=LaunchpadConfig(
                    preset=Preset(name="cpu-small"),
                ),
                apps_config=AppsConfig(
                    llm_config=LLMConfig(
                        model=CustomLLMModel(
                            model_name="my-custom-model",
                            model_apolo_path=ApoloFilesPath(
                                path="storage://cluster/org/project/models/my-model"
                            ),
                            server_extra_args=[
                                "--max-model-len",
                                "4096",
                                "--tensor-parallel-size",
                                "2",
                            ],
                        ),
                        llm_preset=Preset(name="gpu-xlarge"),
                        ui_preset=Preset(name="cpu-small"),
                    ),
                    postgres_config=PostgresConfig(
                        preset=Preset(name="cpu-small"),
                    ),
                    embeddings_config=TextEmbeddingsConfig(
                        model=PreConfiguredEmbeddingsModels.BAAI_BGE_M3,
                        preset=Preset(name="gpu-small"),
                    ),
                ),
            ),
            apolo_client=setup_clients,
            app_type=AppType.Launchpad,
            app_name="launchpad-app",
            namespace="default-namespace",
            app_secrets_name=APP_SECRETS_NAME,
            app_id=APP_ID,
        )


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
                    model=PreConfiguredLLMModels.MAGISTRAL_24B,
                    llm_preset=Preset(name="gpu-medium"),
                    ui_preset=Preset(name="cpu-small"),
                ),
                postgres_config=PostgresConfig(
                    preset=Preset(name="cpu-small"),
                ),
                embeddings_config=TextEmbeddingsConfig(
                    model=PreConfiguredEmbeddingsModels.BAAI_BGE_M3,
                    preset=Preset(name="gpu-small"),
                ),
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

    assert (
        config["vllm"]["hugging_face_model"]["model_hf_name"]
        == "unsloth/Magistral-Small-2506-GGUF"
    )
    assert config["vllm"]["preset"]["name"] == "gpu-medium"
