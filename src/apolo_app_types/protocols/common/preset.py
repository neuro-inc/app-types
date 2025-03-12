from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.input_type import InputType


class Preset(InputType):
    model_config = InputType.model_config | ConfigDict(
        json_schema_extra={
            "x-title": "Presets Configuration",
            "x-description": "Configuration for Apolo presets.",
            "x-logo-url": "https://example.com/logo",
        }
    )
    name: str = Field(..., description="The name of the preset.", title="Preset name")
