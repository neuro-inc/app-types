import base64
import json

import apolo_sdk

from apolo_app_types.protocols.common.containers import DockerConfigModel


async def get_apolo_registry_secrets_value(
    client: apolo_sdk.Client,
) -> DockerConfigModel:
    """
    Get the registry secrets value from the Apolo client.
    """
    user = client.config.username
    token = await client.config.token()
    host = client.config.registry_url.host or ""
    contents = {"auths": {host: {"auth": f"{user}:{token}"}}}
    json_contents = json.dumps(contents)
    return DockerConfigModel(
        filecontents=str(base64.b64encode(json_contents.encode("utf-8")))
    )
