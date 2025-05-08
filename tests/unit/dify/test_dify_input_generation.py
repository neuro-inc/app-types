import pytest

from apolo_app_types import Bucket, CrunchyPostgresUserCredentials
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.common.buckets import BucketProvider, S3BucketCredentials
from apolo_app_types.protocols.dify import (
    DifyAppApi,
    DifyAppInputs,
    DifyAppProxy,
    DifyAppRedis,
    DifyAppWeb,
    DifyAppWorker,
)

from tests.unit.constants import APP_SECRETS_NAME, DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_dify_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=DifyAppInputs(
            ingress_http=IngressHttp(
                clusterName="test",
            ),
            api=DifyAppApi(title="some_title", preset=Preset(name="cpu-small")),
            worker=DifyAppWorker(preset=Preset(name="cpu-small")),
            proxy=DifyAppProxy(preset=Preset(name="cpu-small")),
            web=DifyAppWeb(preset=Preset(name="cpu-small")),
            redis=DifyAppRedis(master_preset=Preset(name="cpu-small")),
            bucket=Bucket(
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
            external_postgres=CrunchyPostgresUserCredentials(
                user="pgvector_user",
                password="pgvector_password",
                host="pgvector_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=4321,
                dbname="db_name",
            ),
            external_pgvector=CrunchyPostgresUserCredentials(
                user="pgvector_user",
                password="pgvector_password",
                host="pgvector_host",
                port=5432,
                pgbouncer_host="pgbouncer_host",
                pgbouncer_port=4321,
                dbname="db_name",
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Dify,
        app_name="dify-app",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["api"]["podLabels"] == {
        "platform.apolo.us/component": "api",
        "platform.apolo.us/preset": "cpu-small",
    }
    assert helm_params["worker"]["podLabels"] == {
        "platform.apolo.us/component": "worker",
        "platform.apolo.us/preset": "cpu-small",
    }
    assert helm_params["proxy"]["podLabels"] == {
        "platform.apolo.us/component": "proxy",
        "platform.apolo.us/preset": "cpu-small",
    }
    assert helm_params["web"]["podLabels"] == {
        "platform.apolo.us/component": "web",
        "platform.apolo.us/preset": "cpu-small",
    }
    assert helm_params["redis"]["master"]["podLabels"] == {
        "platform.apolo.us/component": "redis_master",
        "platform.apolo.us/preset": "cpu-small",
    }
    assert helm_params["externalPostgres"] == {
        "username": "pgvector_user",
        "password": "pgvector_password",
        "address": "pgbouncer_host",
        "port": 4321,
        "dbName": "db_name",
    }
    assert helm_params["externalPgvector"] == {
        "username": "pgvector_user",
        "password": "pgvector_password",
        "address": "pgbouncer_host",
        "port": 4321,
        "dbName": "db_name",
    }
    assert helm_params["redis"]["auth"]["password"]
    assert helm_params["redis"]["architecture"] == "standalone"
    assert helm_params["api"]["secretKey"]
    assert helm_params["api"]["initPassword"]
