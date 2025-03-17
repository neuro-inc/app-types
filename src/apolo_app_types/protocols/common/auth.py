from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import SchemaExtraMetadata


class BasicAuth(BaseModel):
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
