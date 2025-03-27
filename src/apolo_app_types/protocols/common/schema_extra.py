import enum
from typing import Any

from pydantic import BaseModel, Field


class SchemaMetaType(enum.StrEnum):
    INLINE = "inline"
    INTEGRATION = "integration"


class SchemaExtraMetadata(BaseModel):
    title: str = Field(..., alias="x-title")
    description: str = Field(..., alias="x-description")
    meta_type: SchemaMetaType = Field(..., alias="x-meta-type")
    logo_url: str | None = Field(None, alias="x-logo-url")
    model_config = {"populate_by_name": True}

    def as_json_schema_extra(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
