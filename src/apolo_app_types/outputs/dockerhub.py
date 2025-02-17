import base64
import json
import logging
import typing as t

from apolo_app_types import DockerHubOutputs
from apolo_app_types.outputs.utils.parsing import parse_cli_args


logger = logging.getLogger()


async def get_dockerhub_outputs(helm_values: dict[str, t.Any]) -> dict[str, t.Any]:
    cli_args = parse_cli_args(helm_values.get("serverExtraArgs", []))

    user = cli_args["job.args.registry_user"]
    secret = cli_args["job.args.registry_secret"]
    auth64 = base64.b64encode(f"{user}:{secret}".encode())
    dockerhub_outputs = DockerHubOutputs(
        dockerconfigjson=base64.b64encode(
            json.dumps(
                {"auths": {"https://index.docker.io/v1/": {"auth": auth64.decode()}}}
            ).encode()
        ).decode()
    )
    return dockerhub_outputs.model_dump()
