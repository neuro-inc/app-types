from pydantic import BaseModel, Field


class Preset(BaseModel):
    name: str = Field(..., description="The name of the preset.", title="Preset name")

    class Config:
        schema_extra = {
            "description": "Component deployment preset.",
        }
