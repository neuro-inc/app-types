from pydantic import BaseModel, Field


class StorageGB(BaseModel):
    size: int = Field(
        ...,
        description="The size of the storage in GB.",
        title="Storage size",
    )
    # TODO: should be an enum
    storageClassName: str | None = Field(
        default=None,
        description="The storage class name.",
        title="Storage class name",
    )
