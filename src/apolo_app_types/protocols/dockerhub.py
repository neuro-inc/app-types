from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppOutputs,
)
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret


class DockerHubModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="DockerHub",
            description="Configure access to DockerHub for pulling container images.",
        ).as_json_schema_extra(),
    )

    registry_url: str = Field(  # noqa: N815
        default="https://index.docker.io/v1/",
        json_schema_extra=SchemaExtraMetadata(
            title="Registry URL",
            description="Set the Docker registry URL to pull container images from.",
        ).as_json_schema_extra(),
    )

    username: str = Field(  # noqa: N815
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Username",
            description="Provide the DockerHub username used"
            " to authenticate with the registry.",
        ).as_json_schema_extra(),
    )

    password: ApoloSecret = Field(  # noqa: N815
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Password",
            description="Enter the password or secret used"
            " to authenticate with DockerHub.",
        ).as_json_schema_extra(),
    )


class DockerHubInputs(AppInputs):
    dockerhub: DockerHubModel


class DockerConfigModel(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Docker Config",
            description="Docker configuration content.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    filecontents: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Docker Config File Contents",
            description="The contents of the Docker config file.",
        ).as_json_schema_extra(),
    )


class DockerHubOutputs(AppOutputs):
    dockerconfigjson: DockerConfigModel
