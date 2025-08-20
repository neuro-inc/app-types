import base64
import json

import apolo_sdk
from yarl import URL

from apolo_app_types.helm.utils.credentials import get_service_account
from apolo_app_types.protocols.common.containers import DockerConfigModel


async def get_apolo_registry_token(
    client: apolo_sdk.Client, sa_name: str | None
) -> str:
    service_account, _, auth_token = await get_service_account(client, name=sa_name)

    cluster_name = client.config.cluster_name
    org_name = client.config.org_name
    project_name = client.config.project_name

    perm = apolo_sdk.Permission(
        uri=URL(f"image://{cluster_name}/{org_name}/{project_name}"),
        action=apolo_sdk.Action.READ,
    )

    await client.users.share(service_account.role, permission=perm)
    return auth_token


async def get_apolo_registry_secrets_value(
    client: apolo_sdk.Client,
    sa_name: str | None = None,
) -> DockerConfigModel:
    """
    Get the registry secrets value from the Apolo client.
    """
    token = await get_apolo_registry_token(client, sa_name=sa_name)
    host = client.config.registry_url.host or ""
    b64_token = base64.b64encode(f"token:{token}".encode()).decode("utf-8")
    contents = {"auths": {host: {"auth": b64_token}}}
    json_contents = json.dumps(contents)
    return DockerConfigModel(
        filecontents=base64.b64encode(json_contents.encode("utf-8")).decode("utf-8")
    )


async def get_image_docker_url(
    client: apolo_sdk.Client, image: str, tag: str = "latest"
) -> str:
    return client.parse.remote_image(
        f"{image}:{tag}", cluster_name=client.config.cluster_name
    ).as_docker_url()
