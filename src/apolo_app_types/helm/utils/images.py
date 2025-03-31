import base64
import json

import apolo_sdk


async def get_apolo_registry_secrets_value(client: apolo_sdk.Client) -> bytes:
    """
    Get the registry secrets value from the Apolo client.
    """
    async with apolo_sdk.get() as client:
        user = client.config.username
        token = await client.config.token()
        host = client.config.registry_url.host or ""
        contents = {"auths": {host: {"auth": f"{user}:{token}"}}}
        json_contents = json.dumps(contents)
        return base64.b64encode(json_contents.encode("utf-8"))
