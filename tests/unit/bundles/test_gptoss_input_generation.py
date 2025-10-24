from dirty_equals import IsStr

from apolo_app_types import HuggingFaceToken
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.bundles.llm import (
    GPTOSSValueProcessor,
)
from apolo_app_types.helm.apps.common import (
    APOLO_ORG_LABEL,
    APOLO_PROJECT_LABEL,
    APOLO_STORAGE_LABEL,
)
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.bundles.llm import (
    GptOssInputs,
    GptOssSize,
)
from apolo_app_types.protocols.common import ApoloSecret

from tests.unit.constants import APP_ID, APP_SECRETS_NAME, DEFAULT_NAMESPACE


async def test_values_llm_generation_gpu_default_preset(
    setup_clients, mock_get_preset_gpu
):
    model_to_test = GptOssSize.gpt_oss_20b
    preset_name = "t4-medium"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=GptOssInputs(
            size=model_to_test,
            hf_token=HuggingFaceToken(
                token_name="test-token-name", token=ApoloSecret(key="FakeSecret")
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.GptOss,
        app_name="deepseek",
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
        "model": {
            "modelHFName": GPTOSSValueProcessor.model_map[model_to_test].model_hf_name,
            "tokenizerHFName": GPTOSSValueProcessor.model_map[
                model_to_test
            ].model_hf_name,
        },
        "llm": {
            "modelHFName": GPTOSSValueProcessor.model_map[model_to_test].model_hf_name,
            "tokenizerHFName": GPTOSSValueProcessor.model_map[
                model_to_test
            ].model_hf_name,
        },
        "env": {
            "HUGGING_FACE_HUB_TOKEN": {
                "valueFrom": {
                    "secretKeyRef": {"name": "apps-secrets", "key": "FakeSecret"}
                }
            }
        },
        "preset_name": preset_name,
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
                    "host": f"{AppType.GptOss.value}--{APP_ID}.apps.some.org.neu.ro",
                    "paths": [{"path": "/", "pathType": "Prefix", "portName": "http"}],
                }
            ],
        },
        "podAnnotations": {
            APOLO_STORAGE_LABEL: '[{"storage_uri": "storage://cluster/test-org/test-project/llm_bundles", "mount_path": "/root/.cache/huggingface", "mount_mode": "rw"}]'  # noqa: E501
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
            "platform.apolo.us/preset": preset_name,
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
