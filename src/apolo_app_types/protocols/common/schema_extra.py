from typing import Any

from pydantic import BaseModel, Field


class SchemaExtraMetadata(BaseModel):
    title: str = Field(..., alias="x-title")
    description: str = Field(..., alias="x-description")
    logo_url: str | None = Field(None, alias="x-logo-url")

    def as_json_schema_extra(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
