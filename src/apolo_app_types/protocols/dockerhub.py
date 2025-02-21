from pydantic import BaseModel, Field

from apolo_app_types.protocols.common import AppInputsV2, AppOutputsV2


class DockerHubModel(BaseModel):
    registry_url: str = Field(  # noqa: N815
        default="https://index.docker.io/v1/",
        description="The URL of the registry where the container images is stored.",
        title="Registry URL",
    )
    username: str = Field(  # noqa: N815
        ...,
        description="The username to access the registry.",
        title="Username",
    )
    password: str = Field(  # noqa: N815
        ...,
        description="The password to access the registry.",
        title="Password",
    )


class DockerHubInputs(AppInputsV2):
    dockerhub: DockerHubModel


class DockerHubOutputs(AppOutputsV2):
    dockerconfigjson: str = Field(..., title="Docker config JSON")
