import pytest

from apolo_app_types.outputs.spark_job import get_spark_job_outputs


@pytest.mark.asyncio
async def test_spark_job_outputs(setup_clients, mock_kubernetes_client, monkeypatch):
    helm_values = {
        "image": {
            "repository": "myrepo/custom-deployment",
            "tag": "v1.0.0",
        },
    }
    res = await get_spark_job_outputs(helm_values=helm_values)
    assert res == {}
