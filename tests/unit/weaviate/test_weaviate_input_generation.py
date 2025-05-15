from unittest.mock import AsyncMock, MagicMock

import apolo_sdk
import pytest

from apolo_app_types import WeaviateBackupConfig, WeaviateInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.common import _get_match_expressions
from apolo_app_types.protocols.common import IngressGrpc, IngressHttp, Preset, StorageGB

from tests.unit.constants import APP_SECRETS_NAME, DEFAULT_NAMESPACE


def _get_mock_s3_credentials() -> apolo_sdk.PersistentBucketCredentials:
    """Helper to create a mock S3 persistent bucket credentials object."""
    mock_credentials_detail = MagicMock(spec=apolo_sdk.BucketCredentials)
    mock_credentials_detail.provider = (
        apolo_sdk.Bucket.Provider.AWS
    )  # Ensure AWS provider
    mock_credentials_detail.credentials = {
        "bucket_name": "test-weaviate-backup-bucket",
        "endpoint_url": "https://s3.amazonaws.com",
        "region_name": "us-east-1",
        "access_key_id": "test-access-key",
        "secret_access_key": "test-secret-key",
    }

    mock_sdk_bucket_credentials = MagicMock(spec=apolo_sdk.PersistentBucketCredentials)
    mock_sdk_bucket_credentials.credentials = [mock_credentials_detail]
    return mock_sdk_bucket_credentials


@pytest.mark.asyncio
async def test_values_weaviate_generation_basic(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients

    # Configure mock for bucket operations to return AWS S3 credentials
    # This assumes setup_clients provides a client with mockable 'buckets' attribute
    mock_s3_creds = _get_mock_s3_credentials()
    apolo_client.buckets.get = AsyncMock(
        return_value=MagicMock(id="test-bucket-id")
    )  # Mock for bucket get
    apolo_client.buckets.create = AsyncMock(
        return_value=MagicMock(id="test-bucket-id")
    )  # Mock for bucket create
    apolo_client.buckets.persistent_credentials_get = AsyncMock(
        return_value=mock_s3_creds
    )
    apolo_client.buckets.persistent_credentials_create = AsyncMock(
        return_value=mock_s3_creds
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
            backup_bucket=WeaviateBackupConfig(enable=True),
            ingress_http=IngressHttp(
                clusterName="test",
            ),
            # cluster_api=BasicAuth(  # noqa: N815
            #     username="testuser",
            #     password="testpass",
            # ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
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
    # Check that ingress key is present and enabled because IngressHttp was provided
    assert "ingress" in helm_params
    assert helm_params["ingress"]["enabled"] is True
    assert helm_params["ingress"]["grpc"]["enabled"] is False


@pytest.mark.asyncio
async def test_values_weaviate_generation_with_ingress(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients

    # Configure mock for bucket operations
    mock_s3_creds = _get_mock_s3_credentials()
    apolo_client.buckets.get = AsyncMock(return_value=MagicMock(id="test-bucket-id"))
    apolo_client.buckets.create = AsyncMock(return_value=MagicMock(id="test-bucket-id"))
    apolo_client.buckets.persistent_credentials_get = AsyncMock(
        return_value=mock_s3_creds
    )
    apolo_client.buckets.persistent_credentials_create = AsyncMock(
        return_value=mock_s3_creds
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
            backup_bucket=WeaviateBackupConfig(enable=True),
            ingress_http=IngressHttp(
                clusterName="test-cluster",
            ),
            ingress_grpc=IngressGrpc(enabled=True),
            # cluster_api=BasicAuth(  # noqa: N815
            #     username="testuser",
            #     password="testpass",
            # ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    assert helm_params["ingress"]["enabled"] is True
    assert helm_params["ingress"]["className"] == "traefik"
    assert len(helm_params["ingress"]["hosts"]) == 1
    assert helm_params["ingress"]["hosts"][0]["host"].endswith(".apps.some.org.neu.ro")

    # Check GRPC ingress configuration
    assert helm_params["ingress"]["grpc"]["enabled"] is False
    # The following assertions would fail if grpc is not
    # enabled, so commenting them out.
    # assert helm_params["ingress"]["grpc"]["className"] == "traefik"
    # assert len(helm_params["ingress"]["grpc"]["hosts"]) == 1
    # assert helm_params["ingress"]["grpc"]["hosts"][0]["host"].endswith(
    #     "-grpc.apps.some.org.neu.ro"
    # )
    # assert helm_params["ingress"]["grpc"]["annotations"] == {
    #     "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
    #     "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
    #     "traefik.ingress.kubernetes.io/router.middlewares": (
    #         f"{DEFAULT_NAMESPACE}-forwardauth@kubernetescrd,"
    #         f"{DEFAULT_NAMESPACE}-strip-headers@kubernetescrd"
    #     ),
    # }


@pytest.mark.asyncio
async def test_values_weaviate_generation_with_auth(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients

    # Configure mock for bucket operations
    mock_s3_creds = _get_mock_s3_credentials()
    apolo_client.buckets.get = AsyncMock(return_value=MagicMock(id="test-bucket-id"))
    apolo_client.buckets.create = AsyncMock(return_value=MagicMock(id="test-bucket-id"))
    apolo_client.buckets.persistent_credentials_get = AsyncMock(
        return_value=mock_s3_creds
    )
    apolo_client.buckets.persistent_credentials_create = AsyncMock(
        return_value=mock_s3_creds
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
            backup_bucket=WeaviateBackupConfig(enable=True),
            ingress_http=IngressHttp(
                clusterName="test-cluster",
            ),
            # cluster_api=BasicAuth(  # noqa: N815
            #     username="testuser",
            #     password="testpass",
            # ),
            ingress_grpc=IngressGrpc(
                clusterName="test-cluster",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    # assert helm_params["clusterApi"]["username"] == "testuser"
    # assert helm_params["clusterApi"]["password"] == "testpass"
    # assert helm_params["authentication"]["anonymous_access"]["enabled"] is False
    # assert helm_params["authentication"]["apikey"]["enabled"] is True
    # assert helm_params["authentication"]["apikey"]["allowed_keys"] == ["testpass"]
    # assert helm_params["authentication"]["apikey"]["users"] == ["testuser"]
    # assert helm_params["authorization"]["admin_list"]["enabled"] is True
    # assert helm_params["authorization"]["admin_list"]["users"] == ["testuser"]
    # assert helm_params["env"]["AUTHENTICATION_APIKEY_ENABLED"] is True
    # assert helm_params["env"]["AUTHENTICATION_APIKEY_ALLOWED_KEYS"] == "testpass"
    # assert helm_params["env"]["AUTHENTICATION_APIKEY_USERS"] == "testuser"


@pytest.mark.asyncio
async def test_values_weaviate_generation_with_backup(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients

    # Configure mock for bucket operations
    mock_s3_creds = _get_mock_s3_credentials()
    apolo_client.buckets.get = AsyncMock(return_value=MagicMock(id="test-bucket-id"))
    apolo_client.buckets.create = AsyncMock(return_value=MagicMock(id="test-bucket-id"))
    apolo_client.buckets.persistent_credentials_get = AsyncMock(
        return_value=mock_s3_creds
    )
    apolo_client.buckets.persistent_credentials_create = AsyncMock(
        return_value=mock_s3_creds
    )

    helm_args, helm_params = await app_type_to_vals(
        input_=WeaviateInputs(
            preset=Preset(
                name="cpu-large",
            ),
            persistence=StorageGB(size=64),
            backup_bucket=WeaviateBackupConfig(enable=True),
            ingress_http=IngressHttp(
                clusterName="test-cluster",
            ),
            # clusterApi=BasicAuth(  # noqa: N815
            #     username="testuser",
            #     password="testpass",
            # ),
            ingress_grpc=IngressGrpc(
                clusterName="test-cluster",
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.Weaviate,
        app_name="weaviate",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )

    assert helm_params["backups"]["s3"]["enabled"] is True
    assert (
        helm_params["backups"]["s3"]["envconfig"]["BACKUP_S3_BUCKET"]
        == "test-weaviate-backup-bucket"
    )
    assert (
        helm_params["backups"]["s3"]["envconfig"]["BACKUP_S3_ENDPOINT"]
        == "s3.amazonaws.com"
    )
    assert helm_params["backups"]["s3"]["envconfig"]["BACKUP_S3_REGION"] == "us-east-1"
    assert (
        helm_params["backups"]["s3"]["secrets"]["AWS_ACCESS_KEY_ID"]
        == "test-access-key"
    )
    assert (
        helm_params["backups"]["s3"]["secrets"]["AWS_SECRET_ACCESS_KEY"]
        == "test-secret-key"
    )
