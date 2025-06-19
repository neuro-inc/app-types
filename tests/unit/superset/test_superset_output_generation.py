import pytest

from apolo_app_types.outputs.superset import get_superset_outputs


@pytest.mark.asyncio
async def test_superset(setup_clients, mock_kubernetes_client, app_instance_id):
    res = await get_superset_outputs(
        helm_values={
            "extraSecretEnv": {"SUPERSET_SECRET_KEY": "some_key"},
            "init": {
                "adminUser": {
                    "username": "username",
                    "firstname": "Firstname",
                    "lastname": "Lastname",
                    "email": "email@email.ua",
                    "password": "password",
                }
            },
        },
        app_instance_id=app_instance_id,
    )

    assert res
    assert res["secret"] == "some_key"
    assert res["web_app_url"] == {
        "external_url": {
            "base_path": "/",
            "host": "example.com",
            "port": 80,
            "protocol": "https",
            "timeout": 30.0,
        },
        "internal_url": {
            "base_path": "/",
            "host": "app.default-namespace",
            "port": 80,
            "protocol": "http",
            "timeout": 30.0,
        },
    }
    assert res["admin_user"] == {
        "email": "email@email.ua",
        "firstname": "Firstname",
        "lastname": "Lastname",
        "password": "password",
        "username": "username",
    }
