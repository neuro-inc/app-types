import pytest

from apolo_app_types import BasicAuth, Bucket, HuggingFaceModel, WeaviateInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.protocols.common import Ingress, IngressGrpc, Preset, StorageGB
from apolo_app_types.protocols.common.buckets import (
    BucketProvider,
    CredentialsType,
    S3BucketCredentials,
)
from apolo_app_types.protocols.common.secrets import K8sSecret, SecretKeyRef
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
                name="gpu-large",
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
                    modelHFName="test",
                    hfToken=K8sSecret(
                        valueFrom=SecretKeyRef(
                            name="test-secret",
                            key="hf_token",
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
    assert helm_params["env"]["HUGGING_FACE_HUB_TOKEN"] == hf_token


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
                enabled=True,
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
                enabled=True,
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
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
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
                enabled=False,
                clusterName="test",
            ),
            clusterApi=BasicAuth(  # noqa: N815
                username="testuser",
                password="testpass",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
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


@pytest.mark.asyncio
async def test_values_weaviate_generation_with_ingress(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
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
                enabled=True,
                clusterName="test-cluster",
                grpc=IngressGrpc(enabled=True),
            ),
            clusterApi=BasicAuth(  # noqa: N815
                username="testuser",
                password="testpass",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
    )

    assert helm_params["ingress"]["enabled"] is True
    assert helm_params["ingress"]["className"] == "traefik"
    assert len(helm_params["ingress"]["hosts"]) == 1
    assert helm_params["ingress"]["hosts"][0]["host"].endswith(".apps.some.org.neu.ro")

    # Check GRPC ingress configuration
    assert helm_params["ingress"]["grpc"]["enabled"] is True
    assert helm_params["ingress"]["grpc"]["className"] == "traefik"
    assert len(helm_params["ingress"]["grpc"]["hosts"]) == 1
    assert helm_params["ingress"]["grpc"]["hosts"][0]["host"].endswith(
        "-grpc.apps.some.org.neu.ro"
    )
    assert helm_params["ingress"]["grpc"]["annotations"] == {
        "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
        "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
    }


@pytest.mark.asyncio
async def test_values_weaviate_generation_with_auth(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
            ingress=Ingress(
                enabled=True,
                clusterName="test-cluster",
                grpc=IngressGrpc(enabled=True),
            ),
            clusterApi=BasicAuth(  # noqa: N815
                username="testuser",
                password="testpass",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
    )

    assert helm_params["clusterApi"]["username"] == "testuser"
    assert helm_params["clusterApi"]["password"] == "testpass"
    assert helm_params["authentication"]["anonymous_access"]["enabled"] is False
    assert helm_params["authentication"]["apikey"]["enabled"] is True
    assert helm_params["authentication"]["apikey"]["allowed_keys"] == ["testpass"]
    assert helm_params["authentication"]["apikey"]["users"] == ["testuser"]
    assert helm_params["authorization"]["admin_list"]["enabled"] is True
    assert helm_params["authorization"]["admin_list"]["users"] == ["testuser"]
    assert helm_params["env"]["AUTHENTICATION_APIKEY_ENABLED"] is True
    assert helm_params["env"]["AUTHENTICATION_APIKEY_ALLOWED_KEYS"] == "testpass"
    assert helm_params["env"]["AUTHENTICATION_APIKEY_USERS"] == "testuser"


@pytest.mark.asyncio
async def test_values_weaviate_generation_with_backup(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
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
                        endpoint_url="https://storage.test-cluster.org.neu.ro",
                        region_name="us-east-1",
                    )
                ],
                bucket_provider=BucketProvider.AWS,
            ),
            ingress=Ingress(
                enabled=True,
                clusterName="test-cluster",
                grpc=IngressGrpc(enabled=True),
            ),
            clusterApi=BasicAuth(  # noqa: N815
                username="testuser",
                password="testpass",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
    )

    assert helm_params["backups"]["s3"]["enabled"] is True
    assert (
        helm_params["backups"]["s3"]["envconfig"]["BACKUP_S3_BUCKET"]
        == "weaviate-backup"
    )
    assert (
        helm_params["backups"]["s3"]["envconfig"]["BACKUP_S3_ENDPOINT"]
        == "storage.test-cluster.org.neu.ro"
    )
    assert helm_params["backups"]["s3"]["envconfig"]["BACKUP_S3_REGION"] == "us-east-1"
    assert (
        helm_params["backups"]["s3"]["secrets"]["AWS_ACCESS_KEY_ID"] == "access_key_id"
    )
    assert (
        helm_params["backups"]["s3"]["secrets"]["AWS_SECRET_ACCESS_KEY"]
        == "access_secret"
    )
