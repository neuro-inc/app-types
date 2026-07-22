import base64
import json

import apolo_sdk
from yarl import URL

from apolo_app_types.helm.utils.credentials import get_service_account
from apolo_app_types.protocols.common.containers import DockerConfigModel


async def create_apolo_registry_service_account(
    client: apolo_sdk.Client,
    sa_name: str,
    sa_permission: apolo_sdk.Action = apolo_sdk.Action.READ,
) -> str:
    try:
        service_account, _, auth_token = await get_service_account(client, name=sa_name)
    except apolo_sdk.IllegalArgumentError as e:
        if "service account with such name exists" in str(e).lower():
            # if we reconfigure the app, we need to create a new service account
            # since we cannot fetch token for the old one
            await client.service_accounts.rm(sa_name)
            service_account, _, auth_token = await get_service_account(
                client,
                name=sa_name,
            )
        else:
            raise e

    cluster_name = client.config.cluster_name
    org_name = client.config.org_name
    project_name = client.config.project_name

    perm = apolo_sdk.Permission(
        uri=URL(f"image://{cluster_name}/{org_name}/{project_name}"),
        action=sa_permission,
    )

    await client.users.share(service_account.role, permission=perm)
    return auth_token


def build_registry_dockerconfig(
    registry_host: str,
    username: str,
    password: str,
) -> DockerConfigModel:
    """
    Build a base64-encoded dockerconfig.json for a container registry.
    """
    b64_auth = base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")
    contents = {"auths": {registry_host: {"auth": b64_auth}}}
    json_contents = json.dumps(contents)
    return DockerConfigModel(
        filecontents=base64.b64encode(json_contents.encode("utf-8")).decode("utf-8")
    )


async def create_apolo_registry_sa_dockerconfig(
    client: apolo_sdk.Client,
    sa_name: str,
) -> DockerConfigModel:
    """
    Create a Docker config for the Apolo registry.
    """
    token = await create_apolo_registry_service_account(client, sa_name=sa_name)
    assert client.config.registry_url.host
    return build_registry_dockerconfig(
        registry_host=client.config.registry_url.host,
        username="token",
        password=token,
    )


async def get_image_docker_url(
    client: apolo_sdk.Client, image: str, tag: str = "latest"
) -> str:
    return client.parse.remote_image(
        f"{image}:{tag}", cluster_name=client.config.cluster_name
    ).as_docker_url()
