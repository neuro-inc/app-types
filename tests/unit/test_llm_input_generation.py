import pytest

from apolo_app_types import HuggingFaceModel, LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.common.secrets import K8sSecret, Secret, SecretKeyRef
from apolo_app_types.protocols.llm import LLMModel
from tests.unit.constants import CPU_POOL, DEFAULT_NAMESPACE, GPU_POOL


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
                enabled=True,
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
        "grpc": {
            "enabled": False,
        },
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
                name="gpu-small",
            ),
            ingress=Ingress(
                enabled=True,
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
        "grpc": {
            "enabled": False,
        },
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
async def test_values_llm_generation_cpu_k8s_secret(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="cpu-large",
            ),
            ingress=Ingress(
                enabled=True,
                clusterName="test",
            ),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test",
                    modelFiles="test",
                    hfToken=K8sSecret(
                        valueFrom=SecretKeyRef(
                            secretKeyRef=Secret(
                                name="apps-secrets",
                                key="hf_token",
                            )
                        )
                    ),
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
        "grpc": {
            "enabled": False,
        },
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
    assert helm_params["env"]["HUGGING_FACE_HUB_TOKEN"] == {
        "valueFrom": {"secretKeyRef": {"name": "apps-secrets", "key": "hf_token"}}
    }


@pytest.mark.asyncio
async def test_values_llm_generation_gpu_4x(setup_clients, mock_get_preset_gpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(name="gpu-large"),  # triggers nvidia_gpu=4 in conftest
            ingress=Ingress(enabled=True, clusterName="test"),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(modelHFName="test", hfToken="xxx"),
                serverExtraArgs=["--foo"],
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    # Make sure --tensor-parallel-size=4
    assert helm_params["serverExtraArgs"] == ["--foo", "--tensor-parallel-size=4"]


@pytest.mark.asyncio
async def test_values_llm_generation_gpu_8x(setup_clients, mock_get_preset_gpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(name="gpu-xlarge"),  # triggers nvidia_gpu=8 in conftest
            ingress=Ingress(enabled=True, clusterName="test"),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(modelHFName="test2", hfToken="yyy"),
                serverExtraArgs=["--bar"],
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    # Make sure --tensor-parallel-size=8
    assert helm_params["serverExtraArgs"] == ["--bar", "--tensor-parallel-size=8"]


@pytest.mark.asyncio
async def test_values_llm_generation_gpu_8x_pps(setup_clients, mock_get_preset_gpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(name="gpu-xlarge"),  # triggers nvidia_gpu=8 in conftest
            ingress=Ingress(enabled=True, clusterName="test"),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(modelHFName="test2", hfToken="yyy"),
                serverExtraArgs=["--bar", "--pipeline-parallel-size=8"],
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_params["serverExtraArgs"] == ["--bar", "--pipeline-parallel-size=8"]


@pytest.mark.asyncio
async def test_values_llm_generation_gpu_8x_pps_and_tps(
    setup_clients,
    mock_get_preset_gpu,
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(name="gpu-xlarge"),  # triggers nvidia_gpu=8 in conftest
            ingress=Ingress(enabled=True, clusterName="test"),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test2",
                    hfToken="yyy",
                ),
                serverExtraArgs=[
                    "--bar",
                    "--pipeline-parallel-size=8",
                    "--tensor-parallel-size=8",
                ],
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_params["serverExtraArgs"] == [
        "--bar",
        "--pipeline-parallel-size=8",
        "--tensor-parallel-size=8",
    ]
