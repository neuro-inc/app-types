import pytest

from apolo_app_types import HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.llm import LLMInputs, LLMModel
from apolo_app_types.protocols.stable_diffusion import (
    StableDiffusionInputs,
    StableDiffusionParams,
)


CPU_POOL = "cpu_pool"
GPU_POOL = "gpu_pool"
DEFAULT_POOL = "default"
DEFAULT_NAMESPACE = "default"


@pytest.mark.asyncio
async def test_values_llm_generation_cpu(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    hf_token = "test3"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="cpu-large",
            ),
            ingress=Ingress(
                enabled="true",
                clusterName="test",
            ),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test", hfToken=hf_token
                ),
                tokenizerHFName="test_tokenizer",
                serverExtraArgs=["--flag1.1 --flag1.2", "--flag2", "--flag3"],
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_params["serverExtraArgs"] == [
        "--flag1.1 --flag1.2",
        "--flag2",
        "--flag3",
        "--tensor-parallel-size=0",
    ]
    assert helm_params["affinity"]["nodeAffinity"][
        "requiredDuringSchedulingIgnoredDuringExecution"
    ]["nodeSelectorTerms"][0]["matchExpressions"] == _get_match_expressions([CPU_POOL])
    assert helm_params["ingress"] == {
        "className": "traefik",
        "enabled": True,
        "hosts": [
            {
                "host": "default.apps.some.org.neu.ro",
                "paths": [{"path": "/", "pathType": "Prefix"}],
            }
        ],
    }
    assert helm_params["tolerations"] == [
        {
            "effect": "NoSchedule",
            "key": "platform.neuromation.io/job",
            "operator": "Exists",
        },
        {
            "effect": "NoExecute",
            "key": "node.kubernetes.io/not-ready",
            "operator": "Exists",
            "tolerationSeconds": 300,
        },
        {
            "effect": "NoExecute",
            "key": "node.kubernetes.io/unreachable",
            "operator": "Exists",
            "tolerationSeconds": 300,
        },
    ]
    assert "HUGGING_FACE_HUB_TOKEN" in helm_params["env"]
    assert helm_params["env"]["HUGGING_FACE_HUB_TOKEN"] == hf_token


@pytest.mark.asyncio
async def test_values_llm_generation_gpu(setup_clients, mock_get_preset_gpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    hf_token = "test3"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="gpu-large",
            ),
            ingress=Ingress(
                enabled="true",
                clusterName="test",
            ),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test", hfToken=hf_token
                ),
                tokenizerHFName="test_tokenizer",
                serverExtraArgs=["--flag1.1 --flag1.2", "--flag2", "--flag3"],
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_params["serverExtraArgs"] == [
        "--flag1.1 --flag1.2",
        "--flag2",
        "--flag3",
        "--tensor-parallel-size=1",
    ]
    assert helm_params["affinity"]["nodeAffinity"][
        "requiredDuringSchedulingIgnoredDuringExecution"
    ]["nodeSelectorTerms"][0]["matchExpressions"] == _get_match_expressions([GPU_POOL])
    assert helm_params["ingress"] == {
        "className": "traefik",
        "enabled": True,
        "hosts": [
            {
                "host": "default.apps.some.org.neu.ro",
                "paths": [{"path": "/", "pathType": "Prefix"}],
            }
        ],
    }
    assert helm_params["tolerations"] == [
        {
            "effect": "NoSchedule",
            "key": "platform.neuromation.io/job",
            "operator": "Exists",
        },
        {
            "effect": "NoExecute",
            "key": "node.kubernetes.io/not-ready",
            "operator": "Exists",
            "tolerationSeconds": 300,
        },
        {
            "effect": "NoExecute",
            "key": "node.kubernetes.io/unreachable",
            "operator": "Exists",
            "tolerationSeconds": 300,
        },
        {"effect": "NoSchedule", "key": "nvidia.com/gpu", "operator": "Exists"},
    ]
    assert "HUGGING_FACE_HUB_TOKEN" in helm_params["env"]
    assert helm_params["env"]["HUGGING_FACE_HUB_TOKEN"] == hf_token
    assert helm_params["gpuProvider"] == "nvidia"


@pytest.mark.asyncio
async def test_values_sd_generation(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=StableDiffusionInputs(
            preset=Preset(
                name="cpu-large",
            ),
            ingress=Ingress(
                enabled="true",
                clusterName="test",
            ),
            stable_diffusion=StableDiffusionParams(
                replicaCount=1,
                stablestudio=None,
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test", hfToken="test3"
                ),
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.StableDiffusion,
        app_name="sd",
        namespace=DEFAULT_NAMESPACE,
    )

    assert helm_params["preset_name"] == "cpu-large"
    assert helm_params["api"]["resources"]["requests"]["cpu"] == "1000.0m"
    tolerations = helm_params["api"]["tolerations"]
    assert len(tolerations) == 3
    assert {
        "effect": "NoSchedule",
        "key": "platform.neuromation.io/job",
        "operator": "Exists",
    } in tolerations
    assert {
        "effect": "NoExecute",
        "key": "node.kubernetes.io/not-ready",
        "operator": "Exists",
        "tolerationSeconds": 300,
    } in tolerations
    assert {
        "effect": "NoExecute",
        "key": "node.kubernetes.io/unreachable",
        "operator": "Exists",
        "tolerationSeconds": 300,
    } in tolerations
    match_expressions = helm_params["api"]["affinity"]["nodeAffinity"][
        "requiredDuringSchedulingIgnoredDuringExecution"
    ]["nodeSelectorTerms"][0]["matchExpressions"]
    assert match_expressions == _get_match_expressions([CPU_POOL])
    assert "--api" in helm_params["api"]["env"]["COMMANDLINE_ARGS"]
    assert "--no-download-sd-model" in helm_params["api"]["env"]["COMMANDLINE_ARGS"]
    assert (
        "--lowvram --use-cpu all --no-half --precision full"
        in helm_params["api"]["env"]["COMMANDLINE_ARGS"]
    )
    assert helm_params["api"]["resources"]["requests"].get("nvidia.com/gpu") is None
    assert helm_params["api"]["resources"]["limits"].get("nvidia.com/gpu") is None


@pytest.mark.asyncio
async def test_values_sd_generation_with_gpu(setup_clients, mock_get_preset_gpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=StableDiffusionInputs(
            preset=Preset(
                name="gpu_preset",
            ),
            ingress=Ingress(
                enabled="true",
                clusterName="test",
            ),
            stable_diffusion=StableDiffusionParams(
                replicaCount=1,
                stablestudio=None,
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test", hfToken="test3"
                ),
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.StableDiffusion,
        app_name="sd",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_params["preset_name"] == "gpu_preset"
    assert helm_params["api"]["resources"]["requests"]["cpu"] == "1000.0m"
    assert helm_params["api"]["resources"]["requests"]["nvidia.com/gpu"] == "1"
    tolerations = helm_params["api"]["tolerations"]
    assert len(tolerations) == 4
    assert {
        "effect": "NoSchedule",
        "key": "platform.neuromation.io/job",
        "operator": "Exists",
    } in tolerations
    assert {
        "effect": "NoExecute",
        "key": "node.kubernetes.io/not-ready",
        "operator": "Exists",
        "tolerationSeconds": 300,
    } in tolerations
    assert {
        "effect": "NoExecute",
        "key": "node.kubernetes.io/unreachable",
        "operator": "Exists",
        "tolerationSeconds": 300,
    } in tolerations
    assert {
        "effect": "NoSchedule",
        "key": "nvidia.com/gpu",
        "operator": "Exists",
    } in tolerations
    match_expressions = helm_params["api"]["affinity"]["nodeAffinity"][
        "requiredDuringSchedulingIgnoredDuringExecution"
    ]["nodeSelectorTerms"][0]["matchExpressions"]
    assert match_expressions == _get_match_expressions(["gpu_pool"])
    assert "--api" in helm_params["api"]["env"]["COMMANDLINE_ARGS"]
    assert "--no-download-sd-model" in helm_params["api"]["env"]["COMMANDLINE_ARGS"]
    assert (
        "--lowvram --use-cpu all --no-half --precision full"
        not in helm_params["api"]["env"]["COMMANDLINE_ARGS"]
    )
