import base64
import json
import logging
import typing as t

from apolo_app_types import DockerConfigModel, DockerHubOutputs


logger = logging.getLogger()


async def get_dockerhub_outputs(
    helm_values: dict[str, t.Any], app_instance_id: str
) -> dict[str, t.Any]:
    user = helm_values["job"]["args"]["registry_user"]
    secret = helm_values["job"]["args"]["registry_secret"]
    auth64 = base64.b64encode(f"{user}:{secret}".encode())
    dockerhub_outputs = DockerHubOutputs(
        dockerconfigjson=DockerConfigModel(
            filecontents=base64.b64encode(
                json.dumps(
                    {
                        "auths": {
                            "https://index.docker.io/v1/": {"auth": auth64.decode()}
                        }
                    }
                ).encode()
            ).decode()
        )
    )
    return dockerhub_outputs.model_dump()
