from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


class AppInstance(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="App Instance",
            description="Reference to an application instance.",
        ).as_json_schema_extra(),
    )
    app_id: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Application ID",
            description="The unique identifier of the application instance.",
        ).as_json_schema_extra(),
    )
    app_name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Application Name",
            description="The name of the application instance.",
        ).as_json_schema_extra(),
    )
