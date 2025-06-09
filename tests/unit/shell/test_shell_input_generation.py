import json

import pytest

from apolo_app_types import ShellAppInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Preset

from tests.unit.constants import (
    APP_SECRETS_NAME,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_NAMESPACE,
    DEFAULT_ORG_NAME,
    DEFAULT_PROJECT_NAME,
)


@pytest.mark.asyncio
async def test_shell_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=ShellAppInputs(
            preset=Preset(name="cpu-small"),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Shell,
        app_name="shell-app",
        namespace=DEFAULT_NAMESPACE,
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/web-shell",
        "tag": "pipelines",
        "pullPolicy": "IfNotPresent",
    }

    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"containerPort": 7681, "name": "http"}],
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = json.loads(storage_json)
    assert len(parsed_storage) == 1

    assert parsed_storage[0]["storage_uri"] == (
        f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{DEFAULT_PROJECT_NAME}/"
        f".apps/shell/shell-app"
    )
    assert parsed_storage[0]["mount_path"] == "/var/storage"
    assert parsed_storage[0]["mount_mode"] == "r"

    pod_labels = helm_params.get("podLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"
