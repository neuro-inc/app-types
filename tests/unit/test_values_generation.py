import pytest

from apolo_app_types import HuggingFaceModel, WeaviateInputs, Bucket, BasicAuth
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.protocols.common import Ingress, Preset, StorageGB
from apolo_app_types.protocols.common.buckets import S3BucketCredentials, BucketProvider, CredentialsType
from apolo_app_types.protocols.llm import LLMInputs, LLMModel
from apolo_app_types.protocols.stable_diffusion import (
    StableDiffusionInputs,
    StableDiffusionParams,
)
from apolo_app_types.protocols.weaviate import WEAVIATE_MIN_GB_STORAGE

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



@pytest.mark.asyncio
async def test_values_weaviate_generation_basic(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu_preset",
            ),
            persistence=StorageGB(
                size=32
            ),
            backup_bucket=Bucket(
                id="weaviate-backup",
                owner="owner",
                details={},
                credentials=[
                    S3BucketCredentials(
                        name="name",
                        type=CredentialsType.READ_ONLY,
                        access_key_id="access_key_id",
                        secret_access_key="access_secret",
                        endpoint_url="https://s3-endpoint.com",
                        region_name="us-east-1",
                        )
                ],
                bucket_provider=BucketProvider.AWS,
            ),
            ingress=Ingress(
                enabled="true",
                clusterName="test",
            ),
            clusterApi=BasicAuth(  # noqa: N815
                username="testuser",
                password="testpass",
            ),
        ),
        apolo_client = apolo_client,
        app_type = AppType.Weaviate,
        app_name = "weaviate",
        namespace = DEFAULT_NAMESPACE,
    )

    assert helm_params["resources"]["requests"]["cpu"] == "1000.0m"
    assert helm_params["storage"]["size"] == "64Gi"
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
    match_expressions = helm_params["affinity"]["nodeAffinity"][
        "requiredDuringSchedulingIgnoredDuringExecution"
    ]["nodeSelectorTerms"][0]["matchExpressions"]
    assert match_expressions == _get_match_expressions(["cpu_pool"])
    assert helm_params["ingress"]["enabled"] is False
    assert helm_params["ingress"]["grpc"]["enabled"] is False
#
#
# @pytest.mark.asyncio
# async def test_values_weaviate_generation_with_ingress(
#     setup_clients, mock_get_preset_cpu
# ):
#     from apolo_app_types.app_types import AppType
#
#     from mlops_deployer.args import _generate_extra_installation_values
#
#     async for apolo_client, apps_client in setup_clients:
#         result = await _generate_extra_installation_values(
#             helm_args=[
#                 "--set preset_name=cpu-large",
#                 "--set ingress.enabled=true",
#                 "--set ingress.clusterName=test-cluster",
#                 "--set ingress.grpc.enabled=true",
#             ],
#             apolo_client=apolo_client,
#             apps_client=apps_client,
#             app_type=AppType.Weaviate,
#             app_name="weaviate",
#         )
#         yaml_path = result[-1]
#
#         data = await _read_yaml(yaml_path)
#         assert data["ingress"]["enabled"] is True
#         assert data["ingress"]["className"] == "traefik"
#         assert len(data["ingress"]["hosts"]) == 1
#         assert data["ingress"]["hosts"][0]["host"].endswith(".apps.some.org.neu.ro")
#
#         # Check GRPC ingress configuration
#         assert data["ingress"]["grpc"]["enabled"] is True
#         assert data["ingress"]["grpc"]["className"] == "traefik"
#         assert len(data["ingress"]["grpc"]["hosts"]) == 1
#         assert data["ingress"]["grpc"]["hosts"][0]["host"].endswith(
#             "-grpc.apps.some.org.neu.ro"
#         )
#         assert data["ingress"]["grpc"]["annotations"] == {
#             "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
#             "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
#         }
#
#
# @pytest.mark.asyncio
# async def test_values_weaviate_generation_with_auth(setup_clients, mock_get_preset_cpu):
#     from apolo_app_types.app_types import AppType
#
#     from mlops_deployer.args import _generate_extra_installation_values
#
#     async for apolo_client, apps_client in setup_clients:
#         result = await _generate_extra_installation_values(
#             helm_args=[
#                 "--set preset_name=cpu-large",
#                 "--set authentication.enabled=true",
#                 "--set clusterApi.username=testuser",
#                 "--set clusterApi.password=testpass",
#             ],
#             apolo_client=apolo_client,
#             apps_client=apps_client,
#             app_type=AppType.Weaviate,
#             app_name="weaviate",
#         )
#         yaml_path = result[-1]
#
#         data = await _read_yaml(yaml_path)
#         assert data["clusterApi"]["username"] == "testuser"
#         assert data["clusterApi"]["password"] == "testpass"
#         assert data["authentication"]["anonymous_access"]["enabled"] is False
#         assert data["authentication"]["apikey"]["enabled"] is True
#         assert data["authentication"]["apikey"]["allowed_keys"] == ["testpass"]
#         assert data["authentication"]["apikey"]["users"] == ["testuser"]
#         assert data["authorization"]["admin_list"]["enabled"] is True
#         assert data["authorization"]["admin_list"]["users"] == ["testuser"]
#         assert data["env"]["AUTHENTICATION_APIKEY_ENABLED"] is True
#         assert data["env"]["AUTHENTICATION_APIKEY_ALLOWED_KEYS"] == "testpass"
#         assert data["env"]["AUTHENTICATION_APIKEY_USERS"] == "testuser"
#
#
# @pytest.mark.asyncio
# async def test_values_weaviate_generation_with_backup(
#     mock_buckets, mock_get_preset_cpu
# ):
#     from apolo_app_types.app_types import AppType
#
#     from mlops_deployer.args import _generate_extra_installation_values
#
#     async for apolo_client, apps_client in mock_buckets:
#         result = await _generate_extra_installation_values(
#             helm_args=[
#                 "--set preset_name=cpu-large",
#                 "--set backups.enabled=true",
#             ],
#             apolo_client=apolo_client,
#             apps_client=apps_client,
#             app_type=AppType.Weaviate,
#             app_name="weaviate",
#         )
#         yaml_path = result[-1]
#
#         data = await _read_yaml(yaml_path)
#         assert data["backups"]["s3"]["enabled"] is True
#         assert (
#             data["backups"]["s3"]["envconfig"]["BACKUP_S3_BUCKET"] == "weaviate-backup"
#         )
#         assert (
#             data["backups"]["s3"]["envconfig"]["BACKUP_S3_ENDPOINT"]
#             == "storage.test-cluster.org.neu.ro"
#         )
#         assert data["backups"]["s3"]["envconfig"]["BACKUP_S3_REGION"] == "us-east-1"
#         assert (
#             data["backups"]["s3"]["secrets"]["AWS_ACCESS_KEY_ID"] == "test-access-key"
#         )
#         assert (
#             data["backups"]["s3"]["secrets"]["AWS_SECRET_ACCESS_KEY"]
#             == "test-secret-key"
#         )
#
#
# @pytest.mark.asyncio
# async def test_values_weaviate_generation_without_preset(
#     setup_clients, mock_get_preset_cpu
# ):
#     from apolo_app_types.app_types import AppType
#
#     from mlops_deployer.args import _generate_extra_installation_values
#
#     async for apolo_client, apps_client in setup_clients:
#         with pytest.raises(Exception) as exc_info:
#             await _generate_extra_installation_values(
#                 helm_args=[],
#                 apolo_client=apolo_client,
#                 apps_client=apps_client,
#                 app_type=AppType.Weaviate,
#                 app_name="weaviate",
#             )
#         assert str(exc_info.value) == "Missing required key preset_name in helm args."
#
