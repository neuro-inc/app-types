import base64

import pydantic
import pytest

from apolo_app_types import Bucket, PostgresInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.common.buckets import (
    BucketProvider,
    GCPBucketCredentials,
    MinioBucketCredentials,
    S3BucketCredentials,
)
from apolo_app_types.protocols.postgres import (
    PGBouncer,
    PostgresConfig,
    PostgresDBUser,
    PostgresSupportedVersions,
)

from tests.unit.constants import DEFAULT_NAMESPACE


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
                db_users=[PostgresDBUser(name="some_name", db_names=["some_db"])],
            ),
            pg_bouncer=PGBouncer(
                preset=Preset(
                    name="cpu-large",
                ),
            ),
            backup_bucket=Bucket(
                id="some_id",
                owner="some_owner",
                details={},
                credentials=[
                    S3BucketCredentials(
                        name="some_name",
                        access_key_id="some_access_key",
                        secret_access_key="some_secret_key",
                        endpoint_url="some_endpoint",
                        region_name="some_region",
                    )
                ],
                bucket_provider=BucketProvider.AWS,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
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
        {"name": "some_name", "password": {"type": "AlphaNumeric"}},
    ]


@pytest.mark.asyncio
async def test_values_postgresql_generation_without_user(
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
                db_users=[],
            ),
            pg_bouncer=PGBouncer(
                preset=Preset(
                    name="cpu-large",
                ),
            ),
            backup_bucket=Bucket(
                id="some_id",
                owner="some_owner",
                details={},
                credentials=[
                    S3BucketCredentials(
                        name="some_name",
                        access_key_id="some_access_key",
                        secret_access_key="some_secret_key",
                        endpoint_url="some_endpoint",
                        region_name="some_region",
                    )
                ],
                bucket_provider=BucketProvider.AWS,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
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
    ]
    assert helm_params["s3"] == {
        "bucket": "some_id",
        "endpoint": "some_endpoint",
        "key": "some_access_key",
        "keySecret": "some_secret_key",
        "region": "some_region",
    }


@pytest.mark.asyncio
async def test_values_postgresql_generation_with_gcp_bucket(
    setup_clients, mock_get_preset_cpu
):
    from apolo_app_types.inputs.args import app_type_to_vals

    key_data = "Some string"
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
                db_users=[],
            ),
            pg_bouncer=PGBouncer(
                preset=Preset(
                    name="cpu-large",
                ),
            ),
            backup_bucket=Bucket(
                id="some_id",
                owner="some_owner",
                details={},
                credentials=[
                    GCPBucketCredentials(
                        name="some_name",
                        key_data=base64.b64encode(key_data.encode()),
                    )
                ],
                bucket_provider=BucketProvider.GCP,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
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
    ]
    assert helm_params["gcs"] == {"bucket": "some_id", "key": key_data}


@pytest.mark.asyncio
async def test_values_postgresql_generation_with_minio(
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
                db_users=[],
            ),
            pg_bouncer=PGBouncer(
                preset=Preset(
                    name="cpu-large",
                ),
            ),
            backup_bucket=Bucket(
                id="some_id",
                owner="some_owner",
                details={},
                credentials=[
                    MinioBucketCredentials(
                        name="some_name",
                        access_key_id="some_access_key",
                        secret_access_key="some_secret_key",
                        endpoint_url="some_endpoint",
                        region_name="some_region",
                    )
                ],
                bucket_provider=BucketProvider.MINIO,
            ),
        ),
        apolo_client=apolo_client,
        app_type=AppType.PostgreSQL,
        app_name="psdb",
        namespace=DEFAULT_NAMESPACE,
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
    ]
    assert helm_params["s3"] == {
        "bucket": "some_id",
        "endpoint": "some_endpoint",
        "key": "some_access_key",
        "keySecret": "some_secret_key",
        "region": "some_region",
    }


@pytest.mark.asyncio
async def test_values_postgresql_generation_without_matching_bucket_and_creds(
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
                postgres=PostgresConfig(
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
                backup_bucket=Bucket(
                    id="some_id",
                    owner="some_owner",
                    details={},
                    credentials=[
                        GCPBucketCredentials(
                            name="some_name",
                            key_data="U29tZSB0ZXh0",
                        )
                    ],
                    bucket_provider=BucketProvider.AWS,
                ),
            ),
            apolo_client=apolo_client,
            app_type=AppType.PostgreSQL,
            app_name="psdb",
            namespace=DEFAULT_NAMESPACE,
        )
