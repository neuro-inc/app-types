from datetime import datetime
from unittest.mock import AsyncMock

import apolo_sdk
import pydantic
import pytest

from apolo_app_types import PostgresInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.postgres import (
    PGBackupConfig,
    PGBouncer,
    PostgresConfig,
    PostgresDBUser,
    PostgresSupportedVersions,
)

from tests.unit.constants import APP_ID, APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_values_postgresql_generation(setup_clients, mock_get_preset_cpu):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=PostgresInputs(
            preset=Preset(
                name="cpu-large",
            ),
            postgres_config=PostgresConfig(
                postgres_version=PostgresSupportedVersions.v16,
                instance_replicas=3,
                instance_size=1,
                db_users=[PostgresDBUser(name="somename", db_names=["somedb"])],
            ),
            pg_bouncer=PGBouncer(
                preset=Preset(
                    name="cpu-large",
                ),
            ),
            backup=PGBackupConfig(),
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["features"] == {"AutoCreateUserSchema": "true"}
    assert len(helm_params["instances"]) == 1
    assert helm_params["instances"][0]["name"] == "instance1"
    assert helm_params["instances"][0]["replicas"] == 3
    assert helm_params["instances"][0]["dataVolumeClaimSpec"] == {
        "accessModes": ["ReadWriteOnce"],
        "resources": {"requests": {"storage": "1Gi"}},
    }
    assert helm_params["instances"][0]["metadata"]["labels"] == {
        "platform.apolo.us/app": "crunchypostgresql",
        "platform.apolo.us/component": "app",
        "platform.apolo.us/preset": "cpu-large",
    }
    assert "nodeAffinity" in helm_params["instances"][0]["affinity"]
    assert "podAntiAffinity" in helm_params["instances"][0]["affinity"]
    assert helm_params["users"] == [
        {"name": "postgres"},
        {
            "name": "somename",
            "password": {"type": "AlphaNumeric"},
            "databases": ["somedb"],
        },
    ]
    assert helm_params["gcs"] == {
        "bucket": "test-bucket",
        "key": "bucket-access-key",
    }


@pytest.mark.asyncio
async def test_values_postgresql_generation_with_user(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    _, helm_params = await app_type_to_vals(
        input_=PostgresInputs(
            preset=Preset(
                name="cpu-large",
            ),
            postgres_config=PostgresConfig(
                postgres_version=PostgresSupportedVersions.v16,
                instance_replicas=3,
                instance_size=1,
                db_users=[PostgresDBUser(name="user1", db_names=["db1"])],
            ),
            pg_bouncer=PGBouncer(
                preset=Preset(
                    name="cpu-large",
                ),
            ),
            backup=None,
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["features"] == {"AutoCreateUserSchema": "true"}
    assert len(helm_params["instances"]) == 1
    assert helm_params["instances"][0]["name"] == "instance1"
    assert helm_params["instances"][0]["replicas"] == 3
    assert helm_params["instances"][0]["dataVolumeClaimSpec"] == {
        "accessModes": ["ReadWriteOnce"],
        "resources": {"requests": {"storage": "1Gi"}},
    }
    assert helm_params["instances"][0]["metadata"]["labels"] == {
        "platform.apolo.us/app": "crunchypostgresql",
        "platform.apolo.us/component": "app",
        "platform.apolo.us/preset": "cpu-large",
    }
    assert "nodeAffinity" in helm_params["instances"][0]["affinity"]
    assert "podAntiAffinity" in helm_params["instances"][0]["affinity"]
    assert helm_params["users"] == [
        {"name": "postgres"},
        {"databases": ["db1"], "name": "user1", "password": {"type": "AlphaNumeric"}},
    ]
    assert "s3" not in helm_params
    assert "gcs" not in helm_params
    assert "azure" not in helm_params


@pytest.mark.asyncio
async def test_values_postgresql_generation_without_user(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    with pytest.raises(pydantic.ValidationError):
        _, helm_params = await app_type_to_vals(
            input_=PostgresInputs(
                preset=Preset(
                    name="cpu-large",
                ),
                postgres_config=PostgresConfig(
                    postgres_version=PostgresSupportedVersions.v16,
                    instance_replicas=3,
                    instance_size=1,
                    db_users=[],
                ),
                pg_bouncer=PGBouncer(
                    preset=Preset(
                        name="cpu-large",
                    ),
                ),
                backup=None,
            ),
            apolo_client=apolo_client,
            app_type=AppType.PostgreSQL,
            app_name="psdb",
            namespace=DEFAULT_NAMESPACE,
            app_secrets_name=APP_SECRETS_NAME,
            app_id=APP_ID,
        )


@pytest.mark.asyncio
async def test_values_postgresql_generation_with_postgres_user(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    with pytest.raises(pydantic.ValidationError):
        _, helm_params = await app_type_to_vals(
            input_=PostgresInputs(
                preset=Preset(
                    name="cpu-large",
                ),
                postgres_config=PostgresConfig(
                    postgres_version=PostgresSupportedVersions.v16,
                    instance_replicas=3,
                    instance_size=1,
                    db_users=[PostgresDBUser(name="postgres", db_names=["postgres"])],
                ),
                pg_bouncer=PGBouncer(
                    preset=Preset(
                        name="cpu-large",
                    ),
                ),
                backup=None,
            ),
            apolo_client=apolo_client,
            app_type=AppType.PostgreSQL,
            app_name="psdb",
            namespace=DEFAULT_NAMESPACE,
            app_secrets_name=APP_SECRETS_NAME,
            app_id=APP_ID,
        )


@pytest.mark.asyncio
async def test_values_postgresql_generation_with_minio(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    apolo_client = setup_clients
    mock_bucket = apolo_sdk.Bucket(
        id="bucket-id",
        owner="owner",
        cluster_name="cluster",
        org_name="test-org",
        project_name="test-project",
        provider=apolo_sdk.Bucket.Provider.MINIO,
        created_at=datetime.today(),
        imported=False,
        name="test-bucket",
    )
    apolo_client.buckets.get = AsyncMock(return_value=mock_bucket)

    p_credentials = apolo_sdk.PersistentBucketCredentials(
        id="cred-id",
        owner="owner",
        cluster_name="cluster",
        name="test-creds",
        read_only=False,
        credentials=[
            apolo_sdk.BucketCredentials(
                bucket_id="bucket-id",
                provider=apolo_sdk.Bucket.Provider.MINIO,
                credentials={
                    "bucket_name": "test-bucket",
                    "endpoint_url": "test-endpoint",
                    "region_name": "test-region",
                    "access_key_id": "test-access-key",
                    "secret_access_key": "test-secret-key",
                },
            ),
        ],
    )
    apolo_client.buckets.persistent_credentials_get = AsyncMock(
        return_value=p_credentials
    )

    _, helm_params = await app_type_to_vals(
        input_=PostgresInputs(
            preset=Preset(name="cpu-large"),
            postgres_config=PostgresConfig(
                postgres_version=PostgresSupportedVersions.v16,
                instance_replicas=3,
                instance_size=1,
                db_users=[PostgresDBUser(name="user1", db_names=["db1"])],
            ),
            pg_bouncer=PGBouncer(preset=Preset(name="cpu-large")),
            backup=PGBackupConfig(),
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["features"] == {"AutoCreateUserSchema": "true"}
    assert len(helm_params["instances"]) == 1
    assert helm_params["instances"][0]["name"] == "instance1"
    assert helm_params["instances"][0]["replicas"] == 3
    assert helm_params["instances"][0]["dataVolumeClaimSpec"] == {
        "accessModes": ["ReadWriteOnce"],
        "resources": {"requests": {"storage": "1Gi"}},
    }
    assert helm_params["instances"][0]["metadata"]["labels"] == {
        "platform.apolo.us/app": "crunchypostgresql",
        "platform.apolo.us/component": "app",
        "platform.apolo.us/preset": "cpu-large",
    }
    assert "nodeAffinity" in helm_params["instances"][0]["affinity"]
    assert "podAntiAffinity" in helm_params["instances"][0]["affinity"]
    assert helm_params["users"] == [
        {"name": "postgres"},
        {"databases": ["db1"], "name": "user1", "password": {"type": "AlphaNumeric"}},
    ]
    assert helm_params["s3"] == {
        "bucket": "test-bucket",
        "endpoint": "test-endpoint",
        "key": "test-access-key",
        "keySecret": "test-secret-key",
        "region": "test-region",
    }


# Disabled while we don't have proper buckets integration
# @pytest.mark.asyncio
# async def test_values_postgresql_generation_without_matching_bucket_and_creds(
#     setup_clients, mock_get_preset_cpu
# ):
#     from apolo_app_types.inputs.args import app_type_to_vals

#     apolo_client = setup_clients
#     with pytest.raises(pydantic.ValidationError):
#         _, helm_params = await app_type_to_vals(
#             input_=PostgresInputs(
#                 preset=Preset(
#                     name="cpu-large",
#                 ),
#                 postgres=PostgresConfig(
#                     postgres_version=PostgresSupportedVersions.v16,
#                     instance_replicas=3,
#                     instance_size=1,
#                     db_users=[],
#                 ),
#                 pg_bouncer=PGBouncer(
#                     preset=Preset(
#                         name="cpu-large",
#                     ),
#                 ),
#                 backup_bucket=Bucket(
#                     id="some_id",
#                     owner="some_owner",
#                     details={},
#                     credentials=[
#                         GCPBucketCredentials(
#                             name="some_name",
#                             key_data="U29tZSB0ZXh0",
#                         )
#                     ],
#                     bucket_provider=BucketProvider.AWS,
#                 ),
#             ),
#             apolo_client=apolo_client,
#             app_type=AppType.PostgreSQL,
#             app_name="psdb",
#             namespace=DEFAULT_NAMESPACE,
#             app_secrets_name=APP_SECRETS_NAME,
#         )
