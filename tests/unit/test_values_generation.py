import typing as t
from unittest.mock import AsyncMock

import aiofiles
import pytest
import yaml
from apolo_app_types import HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.protocols.common import Preset, Ingress

from apolo_app_types.protocols.llm import LLMInputs, LLMModel

CPU_POOL = "cpu_pool"
DEFAULT_POOL = "default"
DEFAULT_NAMESPACE = "default"


# @pytest.mark.asyncio
# async def test_values_llm_generation(setup_clients, mock_get_preset_cpu):
#     from mlops_deployer.args import _generate_extra_installation_values
#     from mlops_deployer.helm.apps.common import _get_match_expressions
#
#     async for apolo_client, apps_client in setup_clients:
#         result = await _generate_extra_installation_values(
#             helm_args=[
#                 "--set preset_name=cpu-large",
#             ],
#             apolo_client=apolo_client,
#             apps_client=apps_client,
#             app_type=AppType.LLMInference,
#             app_name="llm",
#         )
#         yaml_path = result[-1]
#
#         data = await _read_yaml(yaml_path)
#         assert data["affinity"]["nodeAffinity"][
#             "requiredDuringSchedulingIgnoredDuringExecution"
#         ]["nodeSelectorTerms"][0]["matchExpressions"] == _get_match_expressions(
#             [CPU_POOL]
#         )
#

@pytest.mark.asyncio
async def test_values_llm_generation_without_preset(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

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
                    modelHFName="test",
                    hfToken="test3"
                ),
                tokenizerHFName="test_tokenizer",
                serverExtraArgs=["--flag1.1 --flag1.2", "--flag2", "--flag3"]
            )
        ),
        apolo_client=apolo_client,
        app_type=AppType.LLMInference,
        app_name="llm",
        namespace=DEFAULT_NAMESPACE,
    )
    assert helm_params["serverExtraArgs"] == [
        "--flag1.1 --flag1.2", "--flag2", "--flag3", "--tensor-parallel-size=0"
    ]
    assert helm_params["affinity"]["nodeAffinity"][
               "requiredDuringSchedulingIgnoredDuringExecution"
           ]["nodeSelectorTerms"][0]["matchExpressions"] == _get_match_expressions(
        [CPU_POOL]
    )
    assert helm_params["ingress"] == {
        'className': 'traefik', 'enabled': True,
        'hosts': [{'host': 'default.apps.some.org.neu.ro', 'paths': [{'path': '/', 'pathType': 'Prefix'}]}]
    }
    assert helm_params["tolerations"] == [
        {'effect': 'NoSchedule', 'key': 'platform.neuromation.io/job', 'operator': 'Exists'},
        {'effect': 'NoExecute', 'key': 'node.kubernetes.io/not-ready', 'operator': 'Exists', 'tolerationSeconds': 300},
        {'effect': 'NoExecute', 'key': 'node.kubernetes.io/unreachable', 'operator': 'Exists', 'tolerationSeconds': 300}
    ]
