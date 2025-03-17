from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import SchemaExtraMetadata


class Preset(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Preset",
            description="Configuration for Apolo presets.",
        ).as_json_schema_extra(),
    )
    name: str = Field(..., description="The name of the preset.", title="Preset name")
