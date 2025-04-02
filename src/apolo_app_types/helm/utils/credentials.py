import base64
import json

import apolo_sdk


async def get_service_account(
    client: apolo_sdk.Client, name: str | None = None
) -> tuple[apolo_sdk.ServiceAccount, str, str]:
    """
    Get the service account name from the Apolo client.

    Args:
        client: The Apolo client instance.
        name: The name of the service account. If None, a random name will be generated.
    Returns:
        A tuple containing the service account object, the token, and the auth token.
    """
    sa, token = await client.service_accounts.create(
        name=name,
        default_cluster=client.config.cluster_name,
        default_org=client.config.org_name,
        default_project=client.config.project_name,
    )
    token_data: dict[str, str] = json.loads(base64.b64decode(token.encode()).decode())
    auth_token = token_data["token"]

    return sa, token, auth_token
