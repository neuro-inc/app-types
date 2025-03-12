from apolo_app_types import HuggingFaceModel, LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import ApoloStoragePath, Ingress, Preset
from apolo_app_types.protocols.common.secrets_ import K8sSecret, Secret, SecretKeyRef
from apolo_app_types.protocols.huggingface_storage_cache import (
    HuggingFaceStorageCacheModel,
)
from apolo_app_types.protocols.llm import LLMModel

from tests.unit.constants import CPU_POOL, DEFAULT_NAMESPACE


async def test_values_llm_generation_cpu(setup_clients, mock_get_preset_cpu):
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


async def test_values_llm_generation_gpu(setup_clients, mock_get_preset_gpu):
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
    assert helm_args == [
        "--timeout",
        "30m",
    ]
    assert helm_params == {
        "serverExtraArgs": ["--flag1.1 --flag1.2", "--flag2", "--flag3"],
        "model": {"modelHFName": "test", "tokenizerHFName": "test_tokenizer"},
        "llm": {"modelHFName": "test", "tokenizerHFName": "test_tokenizer"},
        "env": {"HUGGING_FACE_HUB_TOKEN": "test3"},
        "envNvidia": {"CUDA_VISIBLE_DEVICES": "0"},
        "preset_name": "gpu-small",
        "resources": {
            "requests": {"cpu": "1000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
            "limits": {"cpu": "1000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
        },
        "tolerations": [
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
        ],
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "platform.neuromation.io/nodepool",
                                    "operator": "In",
                                    "values": ["gpu_pool"],
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "ingress": {
            "grpc": {"enabled": False},
            "enabled": True,
            "className": "traefik",
            "hosts": [
                {
                    "host": "default.apps.some.org.neu.ro",
                    "paths": [{"path": "/", "pathType": "Prefix"}],
                }
            ],
        },
        "podAnnotations": {},
        "podExtraLabels": {},
        "modelDownload": {"hookEnabled": False, "initEnabled": True},
        "cache": {"enabled": True},
        "gpuProvider": "nvidia",
    }


async def test_values_llm_generation_cpu_k8s_secret(setup_clients, mock_get_preset_cpu):
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
                    hfToken=K8sSecret(
                        valueFrom=SecretKeyRef(
                            secretKeyRef=Secret(
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


async def test_values_llm_generation_gpu_4x(setup_clients, mock_get_preset_gpu):
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


async def test_values_llm_generation_gpu_8x(setup_clients, mock_get_preset_gpu):
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


async def test_values_llm_generation_gpu_8x_pps(setup_clients, mock_get_preset_gpu):
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


async def test_values_llm_generation_gpu_8x_pps_and_tps(
    setup_clients,
    mock_get_preset_gpu,
):
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


async def test_values_llm_generation__storage_integrated(
    setup_clients, mock_get_preset_gpu
):
    hf_token = "test3"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="gpu-small",
            ),
            ingress=Ingress(
                enabled=False,
                clusterName="",
            ),
            llm=LLMModel(
                hugging_face_model=HuggingFaceModel(
                    modelHFName="test", hfToken=hf_token
                ),
            ),
            storage_cache=HuggingFaceStorageCacheModel(
                storage_path=ApoloStoragePath(
                    path="storage://some-cluster/some-org/some-proj/some-folder"
                )
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_args == [
        "--timeout",
        "30m",
    ]
    assert helm_params == {
        "serverExtraArgs": [],
        "model": {"modelHFName": "test", "tokenizerHFName": ""},
        "llm": {"modelHFName": "test", "tokenizerHFName": ""},
        "env": {"HUGGING_FACE_HUB_TOKEN": "test3"},
        "envNvidia": {"CUDA_VISIBLE_DEVICES": "0"},
        "preset_name": "gpu-small",
        "resources": {
            "requests": {"cpu": "1000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
            "limits": {"cpu": "1000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
        },
        "tolerations": [
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
        ],
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "platform.neuromation.io/nodepool",
                                    "operator": "In",
                                    "values": ["gpu_pool"],
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "ingress": {
            "grpc": {"enabled": False},
            "enabled": False,
        },
        "podAnnotations": {
            "platform.apolo.us/inject-storage": '[{"storage_path": "storage://some-cluster/some-org/some-proj/some-folder", "mount_path": "/root/.cache/huggingface", "mount_mode": "rw"}]'  # noqa: E501
        },
        "podExtraLabels": {
            "platform.apolo.us/inject-storage": "true",
        },
        "modelDownload": {"hookEnabled": True, "initEnabled": False},
        "cache": {"enabled": False},
        "gpuProvider": "nvidia",
    }
