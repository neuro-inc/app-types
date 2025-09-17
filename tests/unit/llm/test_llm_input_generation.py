from dirty_equals import IsStr

from apolo_app_types import HuggingFaceModel, HuggingFaceToken, LLMInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import (
    APOLO_ORG_LABEL,
    APOLO_PROJECT_LABEL,
    APOLO_STORAGE_LABEL,
    _get_match_expressions,
)
from apolo_app_types.helm.apps.llm import KEDA_HTTP_PROXY_SERVICE
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import ApoloFilesPath, IngressHttp, Preset
from apolo_app_types.protocols.common.autoscaling import (
    AutoscalingKedaHTTP,
    RequestRateConfig,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.hugging_face import (
    HuggingFaceCache,
)

from tests.unit.constants import APP_ID, APP_SECRETS_NAME, CPU_POOL, DEFAULT_NAMESPACE


async def test_values_llm_generation_cpu(setup_clients, mock_get_preset_cpu):
    hf_token = "test3"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="cpu-large",
            ),
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key=hf_token)
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=["--flag1.1 --flag1.2", "--flag2", "--flag3"],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
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
                "host": f"{AppType.LLMInference.value}--{APP_ID}.apps.some.org.neu.ro",
                "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
            }
        ],
        "annotations": {
            "traefik.ingress.kubernetes.io/router.middlewares": (
                "platform-platform-control-plane-ingress-auth@kubernetescrd"
            )
        },
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
        "valueFrom": {"secretKeyRef": {"name": "apps-secrets", "key": "test3"}}
    }


async def test_values_llm_generation_gpu(setup_clients, mock_get_preset_gpu):
    hf_token = "test3"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="gpu-small",
            ),
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key=hf_token)
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=["--flag1.1 --flag1.2", "--flag2", "--flag3"],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_args == [
        "--timeout",
        "30m",
    ]
    assert helm_params == {
        "serverExtraArgs": ["--flag1.1 --flag1.2", "--flag2", "--flag3"],
        "model": {"modelHFName": "test", "tokenizerHFName": "test_tokenizer"},
        "llm": {"modelHFName": "test", "tokenizerHFName": "test_tokenizer"},
        "env": {
            "HUGGING_FACE_HUB_TOKEN": {
                "valueFrom": {"secretKeyRef": {"name": "apps-secrets", "key": hf_token}}
            }
        },
        "preset_name": "gpu-small",
        "resources": {
            "requests": {"cpu": "2000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
            "limits": {"cpu": "2000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
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
                    "host": f"{AppType.LLMInference.value}--"
                    f"{APP_ID}.apps.some.org.neu.ro",
                    "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
                }
            ],
            "annotations": {
                "traefik.ingress.kubernetes.io/router.middlewares": (
                    "platform-platform-control-plane-ingress-auth@kubernetescrd"
                )
            },
        },
        "podAnnotations": {},
        "podExtraLabels": {},
        "modelDownload": {"hookEnabled": False, "initEnabled": True},
        "cache": {"enabled": True},
        "gpuProvider": "nvidia",
        "podLabels": {
            "platform.apolo.us/component": "app",
            "platform.apolo.us/preset": "gpu-small",
        },
        "appTypesImage": {"tag": IsStr(regex=r"^v\d+\.\d+\.\d+.*$")},
        "apolo_app_id": APP_ID,
        "envNvidia": {
            "PATH": "/usr/local/cuda/bin:/usr/local/sbin:"
            "/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$(PATH)",
            "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:"
            "/usr/local/nvidia/lib64:$(LD_LIBRARY_PATH)",
        },
    }


async def test_values_llm_generation_cpu_apolo_secret(
    setup_clients, mock_get_preset_cpu
):
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="cpu-large",
            ),
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name",
                    token=ApoloSecret(
                        key="hf_token",
                    ),
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=["--flag1.1 --flag1.2", "--flag2", "--flag3"],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
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
                "host": f"{AppType.LLMInference.value}--{APP_ID}.apps.some.org.neu.ro",
                "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
            }
        ],
        "annotations": {
            "traefik.ingress.kubernetes.io/router.middlewares": (
                "platform-platform-control-plane-ingress-auth@kubernetescrd"
            )
        },
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
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key="xxx")
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=["--foo"],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    # Make sure --tensor-parallel-size=4
    assert helm_params["serverExtraArgs"] == ["--foo", "--tensor-parallel-size=4"]


async def test_values_llm_generation_gpu_8x(setup_clients, mock_get_preset_gpu):
    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(name="gpu-xlarge"),  # triggers nvidia_gpu=8 in conftest
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test2",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key="yyy")
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=["--bar"],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    # Make sure --tensor-parallel-size=8
    assert helm_params["serverExtraArgs"] == ["--bar", "--tensor-parallel-size=8"]


async def test_values_llm_generation_gpu_8x_pps(setup_clients, mock_get_preset_gpu):
    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(name="gpu-xlarge"),  # triggers nvidia_gpu=8 in conftest
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test2",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key="yyy")
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=["--bar", "--pipeline-parallel-size=8"],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
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
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test2",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key="yyy")
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            server_extra_args=[
                "--bar",
                "--pipeline-parallel-size=8",
                "--tensor-parallel-size=8",
            ],
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
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
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key=hf_token)
                ),
                hf_cache=HuggingFaceCache(
                    files_path=ApoloFilesPath(
                        path="storage://some-cluster/some-org/some-proj/some-folder"
                    ),
                ),
            ),
            tokenizer_hf_name="",
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_args == [
        "--timeout",
        "30m",
    ]
    assert helm_params == {
        "serverExtraArgs": [],
        "model": {"modelHFName": "test", "tokenizerHFName": ""},
        "llm": {"modelHFName": "test", "tokenizerHFName": ""},
        "env": {
            "HUGGING_FACE_HUB_TOKEN": {
                "valueFrom": {"secretKeyRef": {"name": "apps-secrets", "key": hf_token}}
            }
        },
        "preset_name": "gpu-small",
        "resources": {
            "requests": {"cpu": "2000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
            "limits": {"cpu": "2000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
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
            "enabled": True,
            "grpc": {"enabled": False},
            "annotations": {
                "traefik.ingress.kubernetes.io/router.middlewares": (
                    "platform-platform-control-plane-ingress-auth@kubernetescrd"
                )
            },
            "className": "traefik",
            "hosts": [
                {
                    "host": f"{AppType.LLMInference.value}--"
                    f"{APP_ID}.apps.some.org.neu.ro",
                    "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
                }
            ],
        },
        "podAnnotations": {
            APOLO_STORAGE_LABEL: '[{"storage_uri": "storage://some-cluster/some-org/some-proj/some-folder", "mount_path": "/root/.cache/huggingface", "mount_mode": "rw"}]'  # noqa: E501
        },
        "podExtraLabels": {
            APOLO_STORAGE_LABEL: "true",
            APOLO_ORG_LABEL: "test-org",
            APOLO_PROJECT_LABEL: "test-project",
        },
        "modelDownload": {"hookEnabled": True, "initEnabled": False},
        "cache": {"enabled": False},
        "gpuProvider": "nvidia",
        "podLabels": {
            "platform.apolo.us/component": "app",
            "platform.apolo.us/preset": "gpu-small",
        },
        "appTypesImage": {
            "tag": IsStr(regex=r"^v\d+\.\d+\.\d+.*$"),
        },
        "apolo_app_id": APP_ID,
        "envNvidia": {
            "PATH": "/usr/local/cuda/bin:/usr/local/sbin:"
            "/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$(PATH)",
            "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:"
            "/usr/local/nvidia/lib64:$(LD_LIBRARY_PATH)",
        },
    }


async def test_values_llm_generation__autoscaling(setup_clients, mock_get_preset_gpu):
    hf_token = "test3"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLMInputs(
            preset=Preset(
                name="gpu-small",
            ),
            ingress_http=IngressHttp(),
            hugging_face_model=HuggingFaceModel(
                model_hf_name="test",
                hf_token=HuggingFaceToken(
                    token_name="test-token-name", token=ApoloSecret(key=hf_token)
                ),
                hf_cache=HuggingFaceCache(
                    files_path=ApoloFilesPath(
                        path="storage://some-cluster/some-org/some-proj/some-folder"
                    ),
                ),
            ),
            tokenizer_hf_name="test_tokenizer",
            http_autoscaling=AutoscalingKedaHTTP(
                scaledown_period=400,
                min_replicas=1,
                max_replicas=2,
                request_rate=RequestRateConfig(
                    granularity=1, target_value=2, window_size=1
                ),
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )

    assert helm_params["autoscaling"] == {
        "enabled": True,
        "replicas": {"max": 2, "min": 1},
        "requestRate": {"granularity": "1s", "targetValue": 2, "window": "1s"},
        "scaledownPeriod": 400,
        "externalKedaHttpProxyService": KEDA_HTTP_PROXY_SERVICE,
    }
