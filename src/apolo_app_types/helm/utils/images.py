import asyncio
import base64
import json
import logging

import apolo_sdk
from yarl import URL

from apolo_app_types.helm.utils.credentials import get_service_account
from apolo_app_types.protocols.common.containers import DockerConfigModel
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.github import GithubImageRegistryAuth


logger = logging.getLogger(__name__)

_SECRET_GET_ATTEMPTS = 3
_SECRET_GET_BASE_DELAY_SECONDS = 2


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


async def get_apolo_secret_value(client: apolo_sdk.Client, secret: ApoloSecret) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, _SECRET_GET_ATTEMPTS + 1):
        try:
            value = await client.secrets.get(key=secret.key)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning(
                "Attempt %d/%d to read Apolo secret %r failed: %s",
                attempt,
                _SECRET_GET_ATTEMPTS,
                secret.key,
                exc,
            )
            if attempt < _SECRET_GET_ATTEMPTS:
                await asyncio.sleep(_SECRET_GET_BASE_DELAY_SECONDS * 2 ** (attempt - 1))
        else:
            return value.decode().strip()
    msg = (
        f"Failed to read Apolo secret {secret.key!r}. Ensure the secret "
        "exists in the same cluster, organization and project as this "
        "app installation."
    )
    raise RuntimeError(msg) from last_exc


async def create_github_registry_dockerconfig(
    client: apolo_sdk.Client,
    auth: GithubImageRegistryAuth,
) -> DockerConfigModel:
    token = await get_apolo_secret_value(client, auth.token)
    return build_registry_dockerconfig(
        registry_host=auth.registry_url,
        username=auth.username,
        password=token,
    )


async def get_image_docker_url(
    client: apolo_sdk.Client, image: str, tag: str = "latest"
) -> str:
    return client.parse.remote_image(
        f"{image}:{tag}", cluster_name=client.config.cluster_name
    ).as_docker_url()
