import pytest

from apolo_app_types.outputs.postgres import get_postgres_outputs


@pytest.mark.asyncio
async def test_postgres_outputs(setup_clients, mock_kubernetes_client):
    res = await get_postgres_outputs(helm_values={})
    assert res["postgres_users"]["users"] == {
        "admin": {
            "dbname": "mydatabase",
            "user": "admin",
            "password": "supersecret",
            "host": "db.example.com",
            "port": "5432",
            "pgbouncer_host": "pgbouncer.example.com",
            "pgbouncer_port": "6432",
            "jdbc_uri": "jdbc:postgresql://db.example.com:5432/mydatabase",
            "pgbouncer_jdbc_uri": "jdbc:postgresql://pgbouncer.example.com:6432/mydatabase",
            "pgbouncer_uri": "postgres://pgbouncer.example.com:6432/mydatabase",
            "uri": "postgres://db.example.com:5432/mydatabase",
        }
    }
