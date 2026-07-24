from pydantic import ConfigDict, Field

# Import from submodules directly: protocols.common.containers imports this
# module, so going through protocols.common.__init__ would be circular.
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.base import AppInputs, AppOutputs
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret


GITHUB_AUTH_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="GitHub Auth",
    description="GitHub credentials for API access: username, "
    "personal access token and API URL.",
    meta_type=SchemaMetaType.INTEGRATION,
)

GITHUB_IMAGE_REGISTRY_AUTH_SCHEMA_EXTRA = SchemaExtraMetadata(
    title="GitHub Container Registry Auth",
    description="Credentials for pulling container images from the "
    "GitHub Container Registry (ghcr.io or a GitHub Enterprise Server host).",
    meta_type=SchemaMetaType.INTEGRATION,
)


class GithubCredentials(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="GitHub Credentials",
            description="GitHub username and personal access token.",
        ).as_json_schema_extra(),
    )

    username: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Username",
            description="GitHub account username the personal access token belongs to.",
        ).as_json_schema_extra(),
    )
    token: ApoloSecret = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="GitHub Personal Access Token",
            description="GitHub personal access token (classic). "
            "For pulling container images it needs the read:packages scope, "
            "see https://docs.github.com/en/packages/learn-github-packages/about-permissions-for-github-packages#about-scopes-and-permissions-for-package-registries",
        ).as_json_schema_extra(),
    )


class GithubAuth(GithubCredentials):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=GITHUB_AUTH_SCHEMA_EXTRA.as_json_schema_extra(),
    )

    api_url: str = Field(
        default="https://api.github.com",
        json_schema_extra=SchemaExtraMetadata(
            title="API URL",
            description="GitHub API base URL. Override it for "
            "GitHub Enterprise Server instances.",
        ).as_json_schema_extra(),
    )


class GithubImageRegistryAuth(GithubCredentials):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=(
            GITHUB_IMAGE_REGISTRY_AUTH_SCHEMA_EXTRA.as_json_schema_extra()
        ),
    )

    registry_url: str = Field(
        default="ghcr.io",
        json_schema_extra=SchemaExtraMetadata(
            title="Registry Host",
            description="Container registry host. Use ghcr.io for github.com "
            "or containers.HOSTNAME for GitHub Enterprise Server.",
        ).as_json_schema_extra(),
    )


class GithubAppInputs(AppInputs):
    auth: GithubAuth = Field(
        ...,
        json_schema_extra=GITHUB_AUTH_SCHEMA_EXTRA.model_copy(
            update={"meta_type": SchemaMetaType.INLINE}
        ).as_json_schema_extra(),
    )
    image_registry_auth: GithubImageRegistryAuth = Field(
        ...,
        json_schema_extra=GITHUB_IMAGE_REGISTRY_AUTH_SCHEMA_EXTRA.model_copy(
            update={"meta_type": SchemaMetaType.INLINE}
        ).as_json_schema_extra(),
    )


class GithubAppOutputs(AppOutputs):
    auth: GithubAuth
    image_registry_auth: GithubImageRegistryAuth
