from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class Postgres(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres",
            description="Postgres Configuration.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    platform_app_name: str = Field(
        ...,
        description="The name of the Postgres platform app.",
        title="Platform app name",
    )
    username: str | None = Field(
        None,
        description="The username to access the Postgres database.",
        title="Postgres Username",
    )
    db_name: str | None = Field(
        None,
        description="The name of the Postgres database.",
        title="Postgres Database Name",
    )
