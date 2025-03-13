from pydantic import BaseModel, ConfigDict, Field


class Preset(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "x-title": "Presets Configuration",
            "x-description": "Configuration for Apolo presets.",
            "x-logo-url": "https://example.com/logo",
        }
    )
    name: str = Field(..., description="The name of the preset.", title="Preset name")
