from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppInputsV2,
    AppOutputsV2,
    InputType,
    StrOrSecret,
)


class DockerHubModel(InputType):
    model_config = InputType.model_config | ConfigDict(
        json_schema_extra={
            "x-title": "DockerHub Configuration",
            "x-description": "Configuration for DockerHub.",
            "x-logo-url": "https://example.com/logo",
        }
    )
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
    password: StrOrSecret = Field(  # noqa: N815
        ...,
        description="The password to access the registry.",
        title="Password",
    )


class DockerHubInputs(AppInputsV2):
    dockerhub: DockerHubModel


class DockerConfigModel(BaseModel):
    filecontents: str = Field(
        ...,
        title="Docker config file contents",
        description="The contents of the Docker config file.",
    )


class DockerHubOutputs(AppOutputsV2):
    dockerconfigjson: DockerConfigModel = Field(..., title="Docker config JSON")
