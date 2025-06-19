import json

import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.fooocus import (
    FooocusAppInputs,
    FooocusSpecificAppInputs,
)

from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_ORG_NAME,
    DEFAULT_PROJECT_NAME,
)


@pytest.mark.asyncio
async def test_fooocus_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=FooocusAppInputs(
            preset=Preset(name="cpu-small"),
            ingress_http=IngressHttp(
                clusterName="default",
            ),
            fooocus_specific=FooocusSpecificAppInputs(
                http_auth=True, huggingface_token_secret="RAW_STRING"
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Fooocus,
        app_name="fooocus-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/fooocus",
        "tag": "latest",
        "pullPolicy": "IfNotPresent",
    }

    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 7865}],
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = json.loads(storage_json)
    assert len(parsed_storage) == 2

    assert (
        parsed_storage[0]["storage_uri"]
        == f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{DEFAULT_PROJECT_NAME}/"
        f".apps/fooocus/fooocus-app/data"
    )
    assert parsed_storage[0]["mount_path"] == "/content/data"
    assert parsed_storage[0]["mount_mode"] == "rw"

    assert parsed_storage[1]["storage_uri"] == (
        f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{DEFAULT_PROJECT_NAME}/"
        f".apps/fooocus/fooocus-app/app/outputs"
    )
    assert parsed_storage[1]["mount_path"] == "/content/app/outputs"
    assert parsed_storage[1]["mount_mode"] == "rw"

    pod_labels = helm_params.get("podLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"
