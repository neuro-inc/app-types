import pytest

from apolo_app_types.outputs.spark_job import get_spark_job_outputs


@pytest.mark.asyncio
async def test_spark_job_outputs(
    setup_clients, mock_kubernetes_client, monkeypatch, app_instance_id
):
    helm_values = {
        "image": {
            "repository": "myrepo/custom-deployment",
            "tag": "v1.0.0",
        },
    }
    res = await get_spark_job_outputs(
        helm_values=helm_values, app_instance_id=app_instance_id
    )
    assert res == {}
