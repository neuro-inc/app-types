import base64
import json

import pytest

from apolo_app_types.outputs.dockerhub import get_dockerhub_outputs

from tests.unit.constants import DEFAULT_NAMESPACE


@pytest.mark.asyncio
async def test_dockerhub_outputs(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    res = await get_dockerhub_outputs(
        helm_values={
            "job": {
                "args": {
                    "org": setup_clients.config.org_name,
                    "namespace": DEFAULT_NAMESPACE,
                    "project": setup_clients.config.project_name,
                    "user": setup_clients.username,
                    "registry_name": "DockerHub",
                    "registry_provider_host": "https://index.docker.io/v1/",
                    "registry_api_url": "https://hub.docker.com",
                    "registry_user": "test",
                    "registry_secret": "test",
                }
            }
        },
        app_instance_id=app_instance_id,
    )
    auth64 = base64.b64encode(b"test:test")
    dockerconfigjson = base64.b64encode(
        json.dumps(
            {"auths": {"https://index.docker.io/v1/": {"auth": auth64.decode()}}}
        ).encode()
    ).decode()
    assert res["dockerconfigjson"]["filecontents"] == dockerconfigjson
