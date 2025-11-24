import enum
from typing import Any

from pydantic import BaseModel, Field


X_TITLE_FIELD_NAME = "x-title"
X_DESCRIPTION_FIELD_NAME = "x-description"
X_LOGO_URL_FIELD_NAME = "x-logo-url"
X_META_TYPE_FIELD_NAME = "x-meta-type"
X_IS_CONFIGURABLE_FIELD_NAME = "x-is-configurable"
X_IS_ADVANCED_FIELD_NAME = "x-is-advanced-field"


class SchemaMetaType(enum.StrEnum):
    INLINE = "inline"
    INTEGRATION = "integration"
    DYNAMIC = "dynamic"


class SchemaExtraMetadata(BaseModel):
    title: str = Field(..., alias=X_TITLE_FIELD_NAME)
    description: str = Field(..., alias=X_DESCRIPTION_FIELD_NAME)
    meta_type: SchemaMetaType = Field(
        SchemaMetaType.INLINE, alias=X_META_TYPE_FIELD_NAME
    )
    logo_url: str | None = Field(None, alias=X_LOGO_URL_FIELD_NAME)
    # If field can be collapsed in UI (more advanced setup)
    is_advanced_field: bool = Field(default=False, alias=X_IS_ADVANCED_FIELD_NAME)
    is_configurable: bool = Field(default=True, alias=X_IS_CONFIGURABLE_FIELD_NAME)
    model_config = {"populate_by_name": True}

    def as_json_schema_extra(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
