from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    SchemaExtraMetadata,
    StrOrSecret,
)


class DockerHubModel(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="DockerHub",
            description="Configuration for DockerHub.",
        ).as_json_schema_extra(),
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


class DockerHubInputs(AppInputs):
    dockerhub: DockerHubModel


class DockerConfigModel(BaseModel):
    filecontents: str = Field(
        ...,
        title="Docker config file contents",
        description="The contents of the Docker config file.",
    )


class DockerHubOutputs(AppOutputs):
    dockerconfigjson: DockerConfigModel = Field(..., title="Docker config JSON")
