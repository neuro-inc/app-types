from dirty_equals import IsStr

from apolo_app_types import LLama4Inputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.bundles.llm import Llama4ValueProcessor
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.bundles.llm import Llama4Size
from apolo_app_types.protocols.common import ApoloSecret

from tests.unit.constants import APP_ID, APP_SECRETS_NAME, DEFAULT_NAMESPACE


async def test_values_llm_generation_gpu_default_preset(
    setup_clients, mock_get_preset_gpu
):
    model_to_test = Llama4Size.scout
    preset_a100 = "a100-large"
    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=LLama4Inputs(
            size=model_to_test,
            hf_token=ApoloSecret(key="FakeSecret"),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Llama4,
        app_name="llm4",
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
            "modelHFName": Llama4ValueProcessor.model_map[model_to_test].model_hf_name,
            "tokenizerHFName": Llama4ValueProcessor.model_map[
                model_to_test
            ].model_hf_name,
        },
        "llm": {
            "modelHFName": Llama4ValueProcessor.model_map[model_to_test].model_hf_name,
            "tokenizerHFName": Llama4ValueProcessor.model_map[
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
        "envNvidia": {"CUDA_VISIBLE_DEVICES": "0"},
        "preset_name": preset_a100,
        "resources": {
            "requests": {"cpu": "8000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
            "limits": {"cpu": "8000.0m", "memory": "0M", "nvidia.com/gpu": "1"},
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
            "platform.apolo.us/preset": preset_a100,
        },
        "appTypesImage": {"tag": IsStr(regex=r"^v\d+\.\d+\.\d+.*$")},
        "apolo_app_id": APP_ID,
    }
