import json

import pytest

from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Preset
from apolo_app_types.protocols.jupyter import (
    JupyterAppInputs,
    JupyterSpecificAppInputs,
    JupyterTypes,
)

from tests.unit.constants import (
    APP_SECRETS_NAME,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_ORG_NAME,
    DEFAULT_PROJECT_NAME,
)


@pytest.mark.asyncio
async def test_jupyter_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=JupyterAppInputs(
            preset=Preset(name="cpu-small"),
            jupyter_specific=JupyterSpecificAppInputs(
                jupyter_type=JupyterTypes.LAB,
                http_auth=False,
            ),
        ),
        apolo_client=setup_clients,
        app_type=AppType.Jupyter,
        app_name="jupyter-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/base",
        "tag": "pipelines",
    }

    assert helm_params["service"] == {
        "enabled": True,
        "ports": [{"name": "http", "containerPort": 8888}],
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = json.loads(storage_json)

    assert (
        parsed_storage[0]["storage_uri"]
        == f"storage://{DEFAULT_CLUSTER_NAME}/{DEFAULT_ORG_NAME}/{DEFAULT_PROJECT_NAME}/"
        f".apps/jupyter/jupyter-app/code"
    )
    assert parsed_storage[0]["mount_path"] == "/root/notebooks"
    assert parsed_storage[0]["mount_mode"] == "rw"

    pod_labels = helm_params.get("podLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"
