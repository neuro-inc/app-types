from typing import Any

from pydantic import BaseModel, Field


class DynamicAppIdResponse(BaseModel):
    """Individual item in list response."""

    id: str
    value: Any


class DynamicAppListResponse(BaseModel):
    """Response for list endpoints."""

    status: str
    data: list[DynamicAppIdResponse] | None = None


class DynamicAppBasicResponse(BaseModel):
    """Basic response for health checks."""

    status: str
    data: dict[str, Any] | None = None


class DynamicAppFilterParams(BaseModel):
    """Query parameters for filtering."""

    filter: str | None = Field(None, description="Filter query")
    limit: int = Field(100, gt=0, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
