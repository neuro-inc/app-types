import typing

from pydantic import BaseModel, ConfigDict, Field

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
            title="Env",
            description="K8S container env var.",
        ).as_json_schema_extra(),
    )
    name: str | None = Field(
        default=None,
        title="Deployment Name",
        description="Override name for the deployment",
    )


class Env(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Env",
            description="K8S container env var.",
        ).as_json_schema_extra(),
    )
    name: str
    value: str | int | ApoloSecret | None

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
            title="Container",
            description="K8S container configuration.",
        ).as_json_schema_extra(),
    )
    command: list[str] | None = None
    args: list[str] | None = None
    env: list[Env] = Field(default_factory=list)


class Port(BaseModel):
    name: str = Field(
        default="http",
        title="Port Name",
        description="Name of the port.",
    )
    port: int = Field(
        default=80,
        title="Port",
        description="Port number.",
    )
    path_type: str = Field(
        default="Prefix",
        title="PathType",
        description="Type of path",
    )
    path: str = Field(
        default="/",
        title="Path",
        description="Path for the port.",
    )
