import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.buckets import BucketsAppInputs

from tests.unit.constants import APP_SECRETS_NAME


@pytest.mark.asyncio
async def test_buckets_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=BucketsAppInputs(),
        apolo_client=setup_clients,
        app_type=AppType.Buckets,
        app_name="buckets",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id="buckets-app-id",
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/buckets-app",
        "tag": "latest",
        "pullPolicy": "Always",
    }
    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"containerPort": 8000, "name": "http"}],
    }
    assert helm_params["preset_name"] == "cpu-small"
