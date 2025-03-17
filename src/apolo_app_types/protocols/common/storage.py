import enum

from pydantic import BaseModel, Field, field_validator


class StorageGB(BaseModel):
    size: int = Field(
        ...,
        description="The size of the storage in GB.",
        title="Storage size",
    )
    # TODO: should be an enum
    storageClassName: str | None = Field(  # noqa: N815
        default=None,
        description="The storage class name.",
        title="Storage class name",
    )


class ApoloStoragePath(BaseModel):
    path: str = Field(
        ...,
        description="The path to the Apolo Storage.",
        title="Storage path",
    )

    @field_validator("path", mode="before")
    def validate_storage_path(cls, value: str) -> str:  # noqa: N805
        if not value.startswith("storage://"):
            err_msg = (
                "Storage path must have `storage:` schema and be of absolute path."
            )
            raise ValueError(err_msg)
        return value


class MountPath(BaseModel):
    path: str = Field(
        ...,
        description="The path within a container.",
        title="Mount path",
    )

    @field_validator("path", mode="before")
    def validate_mount_path(cls, value: str) -> str:  # noqa: N805
        if not value.startswith("/"):
            err_msg = "Mount path must be absolute."
            raise ValueError(err_msg)
        return value


class ApoloMountModes(enum.StrEnum):
    RO = "r"
    RW = "rw"


class ApoloMountMode(BaseModel):
    mode: ApoloMountModes = Field(
        default=ApoloMountModes.RW,
        description="The mode of the mount.",
        title="Mount mode",
    )


class ApoloStorageMount(BaseModel):
    storage_path: ApoloStoragePath = Field(
        ...,
        description="The path to the Apolo Storage.",
        title="Storage path",
    )
    mount_path: MountPath = Field(
        ...,
        description="The path within a container.",
        title="Mount path",
    )
    mode: ApoloMountMode = Field(
        default=ApoloMountMode(),
        description="The mode of the mount.",
        title="Mount mode",
    )


class ApoloStorageFile(ApoloStoragePath): ...
