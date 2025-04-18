import apolo_sdk
from yarl import URL


def get_app_data_files_path_url(
    client: apolo_sdk.Client, app_type_name: str, app_name: str
) -> URL:
    return URL(
        f"storage://{client.config.cluster_name}/{client.config.org_name}"
        f"/{client.config.project_name}/.apps/{app_type_name}/{app_name}"
    )


def get_app_data_files_relative_path_url(app_type_name: str, app_name: str) -> URL:
    return URL(f"storage:.apps/{app_type_name}/{app_name}")
