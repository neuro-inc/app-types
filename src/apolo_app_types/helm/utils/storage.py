import apolo_sdk
from pathlib import Path
from apolo_app_types.app_types import AppType


def get_app_data_storage_path(
    client: apolo_sdk.Client, app_type: AppType, app_name: str
) -> Path:
    return Path(
        f"storage://{client.config.cluster_name}/{client.config.org_name}"
        f"/{client.config.project_name}/.apps/{app_type.value}/{app_name}"
    )
