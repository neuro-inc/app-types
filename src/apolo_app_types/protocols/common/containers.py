from enum import StrEnum

from pydantic import ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.dockerhub import DockerConfigModel
from apolo_app_types.protocols.github import GithubImageRegistryAuth


class ContainerImagePullPolicy(StrEnum):
    ALWAYS = "Always"
    NEVER = "Never"
    IF_NOT_PRESENT = "IfNotPresent"


class ContainerImage(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image",
            description="Container image to be used in application",
        ).as_json_schema_extra(),
    )
    repository: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image Repository",
            description="Choose a repository for the container image.",
        ).as_json_schema_extra(),
    )
    tag: str | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image Tag",
            description="Choose a tag for the container image.",
        ).as_json_schema_extra(),
    )
    # Hidden legacy field; superseded by imagepullsecret but still accepted
    # in stored payloads.
    dockerconfigjson: SkipJsonSchema[DockerConfigModel | None] = None
    imagepullsecret: DockerConfigModel | GithubImageRegistryAuth | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Image Pull Secret",
            description="Credentials used to pull the container image from a "
            "private registry: either a Docker config (e.g. from the DockerHub "
            "app) or a GitHub Container Registry auth (from the GitHub app).",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    pull_policy: ContainerImagePullPolicy = Field(
        default=ContainerImagePullPolicy.IF_NOT_PRESENT,
        json_schema_extra=SchemaExtraMetadata(
            title="Container Image Pull Policy",
            description="Specify the pull policy for the container image.",
        ).as_json_schema_extra(),
    )
