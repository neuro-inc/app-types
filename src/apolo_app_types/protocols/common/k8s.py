import typing
from enum import StrEnum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.common.secrets_ import (
    ApoloSecret,
    serialize_optional_secret,
)


class DeploymentName(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Deployment Name",
            description="Set a custom name for the Kubernetes"
            " deployment environment variable.",
        ).as_json_schema_extra(),
    )

    name: str | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Deployment Name",
            description="Provide an override name for the deployment"
            " to customize how it appears in Kubernetes.",
        ).as_json_schema_extra(),
    )


class Env(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Env",
            description="K8S container env var.",
        ).as_json_schema_extra(),
    )
    name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Variable Name",
            description="Specify the name of the environment "
            "variable to inject into the container.",
        ).as_json_schema_extra(),
    )
    value: (
        typing.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="String variable Value",
                    description="Specify the value of the environment variable.",
                ).as_json_schema_extra()
            ),
        ]
        | ApoloSecret
    ) = Field(
        default="",
        json_schema_extra=SchemaExtraMetadata(
            title="Variable Value",
            description="Specify the value of the environment variable.",
        ).as_json_schema_extra(),
    )

    def deserialize_value(self, secret_name: str) -> str | int | dict[str, typing.Any]:
        if self.value is None:
            return ""
        if isinstance(self.value, str | int):
            return self.value
        if isinstance(self.value, ApoloSecret):
            return serialize_optional_secret(
                self.value,
                secret_name=secret_name,
            )
        err_msg = f"Unsupported type for env var value: {type(self.value)}"
        raise ValueError(err_msg)


class Container(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Container Configuration",
            description="Define command, arguments,"
            " and environment variables for the"
            " Kubernetes container.",
        ).as_json_schema_extra(),
    )

    command: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Container Command",
            description="Override the container's default "
            "entrypoint by specifying a custom command.",
        ).as_json_schema_extra(),
    )

    args: list[str] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Container Arguments",
            description="Provide arguments to pass to the "
            "container's entrypoint or command.",
        ).as_json_schema_extra(),
    )

    env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Environment Variables",
            description="Define environment variables to inject into the container.",
        ).as_json_schema_extra(),
    )


class IngressPathTypeEnum(StrEnum):
    PREFIX = "Prefix"
    EXACT = "Exact"
    IMPLEMENTATION_SPECIFIC = "ImplementationSpecific"


class Port(AbstractAppFieldType):
    name: str = Field(
        default="http",
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Port Name",
            description="Specify a name for the HTTP port "
            "(e.g., 'http', 'grpc') to identify it in the service.",
        ).as_json_schema_extra(),
    )

    port: int = Field(
        default=80,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Port",
            description=(
                "Set the HTTP port number that will be exposed from the container. "
                "Please note: platform currently does not allow to expose "
                "multiple ports for a single app on a single domain name. "
                "Please reach us describing your use-case if you need it."
            ),
        ).as_json_schema_extra(),
    )

    path_type: IngressPathTypeEnum = Field(
        default=IngressPathTypeEnum.PREFIX,
        json_schema_extra=SchemaExtraMetadata(
            title="Path Type",
            description="Define how the path should be matched "
            "(e.g., 'Prefix' or 'Exact').",
        ).as_json_schema_extra(),
    )

    path: str = Field(
        default="/",
        json_schema_extra=SchemaExtraMetadata(
            title="Path",
            description="Set the URL path for routing traffic to this port.",
        ).as_json_schema_extra(),
    )
