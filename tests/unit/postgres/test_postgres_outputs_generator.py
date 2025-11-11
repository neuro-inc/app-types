from apolo_app_types.outputs.postgres import get_postgres_outputs


async def test_postgres_outputs(setup_clients, mock_kubernetes_client, app_instance_id):
    res = await get_postgres_outputs(helm_values={}, app_instance_id=app_instance_id)
    assert res["postgres_users"]["users"] == [
        {
            "__type__": "CrunchyPostgresUserCredentials",
            "dbname": "mydatabase",
            "user": "admin",
            "password": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-password-{app_instance_id}",
            },
            "host": "db.example.com",
            "port": 5432,
            "pgbouncer_host": "pgbouncer.example.com",
            "pgbouncer_port": 6432,
            "jdbc_uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-jdbc-uri-{app_instance_id}",
            },
            "pgbouncer_jdbc_uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-pgbouncer-jdbc-uri-{app_instance_id}",
            },
            "pgbouncer_uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-pgbouncer-uri-{app_instance_id}",
            },
            "uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-uri-{app_instance_id}",
            },
            "postgres_uri": {
                "__type__": "PostgresURI",
                "uri": {
                    "__type__": "ApoloSecret",
                    "key": f"postgres-admin-connection-uri-{app_instance_id}",
                },
            },
            "user_type": "user",
        },
        {
            "__type__": "CrunchyPostgresUserCredentials",
            "dbname": "otherdatabase",
            "user": "admin",
            "password": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-password-{app_instance_id}",
            },
            "host": "db.example.com",
            "port": 5432,
            "pgbouncer_host": "pgbouncer.example.com",
            "pgbouncer_port": 6432,
            "jdbc_uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-otherdatabase-jdbc-uri-{app_instance_id}",
            },
            "pgbouncer_jdbc_uri": {
                "__type__": "ApoloSecret",
                "key": (
                    f"postgres-admin-otherdatabase-pgbouncer-jdbc-uri-{app_instance_id}"
                ),
            },
            "pgbouncer_uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-otherdatabase-pgbouncer-uri-{app_instance_id}",
            },
            "uri": {
                "__type__": "ApoloSecret",
                "key": f"postgres-admin-otherdatabase-uri-{app_instance_id}",
            },
            "postgres_uri": {
                "__type__": "PostgresURI",
                "uri": {
                    "__type__": "ApoloSecret",
                    "key": (
                        f"postgres-admin-otherdatabase-connection-uri-{app_instance_id}"
                    ),
                },
            },
            "user_type": "user",
        },
    ]
    mock = mock_kubernetes_client["mock_custom_objects"]
    mock.list_namespaced_custom_object.assert_called_once_with(
        group="postgres-operator.crunchydata.com",
        version="v1beta1",
        namespace="default-namespace",
        plural="postgresclusters",
        label_selector=None,
    )
