from pydantic import BaseModel, Field

from apolo_app_types.protocols.common import AppInputs, AppOutputsV2


class DockerHubModel(BaseModel):
    registry_url: str = Field(  # noqa: N815
        default="https://index.docker.io/v1/",
        description="The URL of the registry where the model is stored.",
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


class DockerHubInputs(AppInputs):
    username: str
    password: str


class DockerHubOutputs(AppOutputsV2):
    dockerconfigjson: str
