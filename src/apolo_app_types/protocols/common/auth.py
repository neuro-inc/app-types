from typing import Literal

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.middleware import AuthIngressMiddleware
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class ApoloAuth(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Platform Authentication",
            description=(
                "Use Apolo platform's built-in authentication and authorization. "
                "Requires authenticated user credentials with appropriate "
                "permissions."
            ),
        ).as_json_schema_extra(),
    )
    type: Literal["apolo_auth"] = Field(
        default="apolo_auth",
        description="Authentication type identifier",
    )


class NoAuth(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="No Authentication",
            description="Disable authentication for this ingress. "
            "The application will be publicly accessible without any authentication.",
        ).as_json_schema_extra(),
    )
    type: Literal["no_auth"] = Field(
        default="no_auth",
        description="Authentication type identifier",
    )


class CustomAuth(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Custom Authentication",
            description=(
                "Use a custom authentication middleware for this ingress. "
                "Allows integration with custom authentication providers."
            ),
        ).as_json_schema_extra(),
    )
    type: Literal["custom_auth"] = Field(
        default="custom_auth",
        description="Authentication type identifier",
    )
    middleware: AuthIngressMiddleware = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Authentication Middleware",
            description="Custom authentication middleware configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )


class BasicAuth(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Basic Auth",
            description="Basic Auth Configuration.",
        ).as_json_schema_extra(),
    )
    username: str = Field(
        default="",
        description="The username for basic authentication.",
        title="Username",
    )
    password: str = Field(
        default="",
        description="The password for basic authentication.",
        title="Password",
    )
