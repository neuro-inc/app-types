from pydantic import BaseModel, ConfigDict, Field


class Preset(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "title": "Presets Configuration",
            "description": "Configuration for Apolo presets.",
            "x-logo-url": "https://example.com/logo",
        },
    )
    name: str = Field(..., description="The name of the preset.", title="Preset name")
