from apolo_app_types.outputs.postgres import get_postgres_outputs


async def test_postgres_outputs(setup_clients, mock_kubernetes_client):
    res = await get_postgres_outputs(helm_values={})
    assert res["postgres_users"]["users"] == [
        {
            "dbname": "mydatabase",
            "user": "admin",
            "password": "supersecret",
            "host": "db.example.com",
            "port": 5432,
            "pgbouncer_host": "pgbouncer.example.com",
            "pgbouncer_port": 6432,
            "jdbc_uri": "jdbc:postgresql://db.example.com:5432/mydatabase",
            "pgbouncer_jdbc_uri": "jdbc:postgresql://pgbouncer.example.com:6432/mydatabase",
            "pgbouncer_uri": "postgres://pgbouncer.example.com:6432/mydatabase",
            "uri": "postgres://db.example.com:5432/mydatabase",
            "postgres_uri": {
                "uri": "postgresql://admin:supersecret@pgbouncer.example.com:6432/mydatabase"
            },
        },
        {
            "dbname": "otherdatabase",
            "user": "admin",
            "password": "supersecret",
            "host": "db.example.com",
            "port": 5432,
            "pgbouncer_host": "pgbouncer.example.com",
            "pgbouncer_port": 6432,
            "jdbc_uri": "jdbc:postgresql://db.example.com:5432/otherdatabase",
            "pgbouncer_jdbc_uri": "jdbc:postgresql://pgbouncer.example.com:6432/otherdatabase",
            "pgbouncer_uri": "postgres://pgbouncer.example.com:6432/otherdatabase",
            "uri": "postgres://db.example.com:5432/otherdatabase",
            "postgres_uri": {
                "uri": "postgresql://admin:supersecret@pgbouncer.example.com:6432/otherdatabase"
            },
        },
    ]
    mock = mock_kubernetes_client["mock_custom_objects"]
    mock.list_namespaced_custom_object.assert_called_once_with(
        group="postgres-operator.crunchydata.com",
        version="v1beta1",
        namespace="default-namespace",
        plural="postgresclusters",
    )
