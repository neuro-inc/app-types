from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.custom_validators import preset_validator
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
)


class Preset(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Resource Preset",
            description="Select the resource preset used per service replica.",
            custom_validators=[preset_validator()],
        ).as_json_schema_extra(),
    )
    name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Resource Preset",
            description="The name of the preset.",
        ).as_json_schema_extra(),
    )
