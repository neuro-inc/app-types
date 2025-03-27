import apolo_sdk

from apolo_app_types.app_types import AppType


def get_app_data_storage_path(
    client: apolo_sdk.Client, app_type: AppType, app_name: str
) -> str:
    return f"storage://{client.config.cluster_name}/{client.config.org_name}/{client.config.project_name}/.apps/{app_type.value}/{app_name}"
