from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class BasicAuth(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Basic Auth",
            description="Basic Auth Configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
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
