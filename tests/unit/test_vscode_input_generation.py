import json

import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    ApoloMountModes,
    MountPath,
)
from apolo_app_types.protocols.vscode import (
    VSCodeAppInputs,
    VSCodeSpecificAppInputs,
)

from tests.unit.constants import (
    APP_SECRETS_NAME,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_ORG_NAME,
    DEFAULT_PROJECT_NAME,
)


@pytest.mark.asyncio
async def test_vscode_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=VSCodeAppInputs(
            preset=Preset(name="cpu-small"),
            vscode_specific=VSCodeSpecificAppInputs(),
        ),
        apolo_client=setup_clients,
        app_type=AppType.VSCode,
        app_name="vscode-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/vscode-server",
        "tag": "development",
        "pullPolicy": "IfNotPresent",
    }

    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8080}],
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = json.loads(storage_json)

    assert (
        parsed_storage[0]["storage_uri"]
        == f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{DEFAULT_PROJECT_NAME}/"
        f".apps/vscode/vscode-app/code"
    )
    assert parsed_storage[0]["mount_path"] == "/home/coder/project"
    assert parsed_storage[0]["mount_mode"] == "rw"

    pod_labels = helm_params.get("podLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"


@pytest.mark.asyncio
async def test_vscode_override_storage_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=VSCodeAppInputs(
            preset=Preset(name="cpu-small"),
            vscode_specific=VSCodeSpecificAppInputs(
                override_code_storage_mount=ApoloFilesMount(
                    storage_uri=ApoloFilesPath(
                        path="storage://test/test/test/.apps/vscode/vscode-app/code"
                    ),
                    mount_path=MountPath(path="/home/coder/directory"),
                    mode=ApoloMountMode(mode=ApoloMountModes.RW),
                )
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.VSCode,
        app_name="vscode-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/vscode-server",
        "tag": "development",
        "pullPolicy": "IfNotPresent",
    }

    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8080}],
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = json.loads(storage_json)

    assert (
        parsed_storage[0]["storage_uri"]
        == "storage://test/test/test/.apps/vscode/vscode-app/code"
    )
    assert parsed_storage[0]["mount_path"] == "/home/coder/directory"
    assert parsed_storage[0]["mount_mode"] == "rw"

    pod_labels = helm_params.get("podLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"
