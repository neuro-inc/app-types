import enum
from typing import Any

from pydantic import BaseModel, Field


class SchemaMetaType(enum.StrEnum):
    INLINE = "inline"
    INTEGRATION = "integration"
    DYNAMIC = "dynamic"


class SchemaExtraMetadata(BaseModel):
    title: str = Field(..., alias="x-title")
    description: str = Field(..., alias="x-description")
    meta_type: SchemaMetaType = Field(SchemaMetaType.INLINE, alias="x-meta-type")
    logo_url: str | None = Field(None, alias="x-logo-url")
    # If field can be collapsed in UI (more advanced setup)
    is_advanced_field: bool = Field(default=False, alias="x-is-advanced-field")
    model_config = {"populate_by_name": True}

    def as_json_schema_extra(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
