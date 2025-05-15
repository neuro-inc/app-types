import enum

import apolo_sdk
from pydantic import ConfigDict, Field, field_validator

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class ApoloFilesPath(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Files Path",
            description="Specify the path within the Apolo "
            "Files application to read from or write to.",
        ).as_json_schema_extra(),
    )

    path: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Path",
            description="Provide the Apolo Storage path starting"
            " with `storage:` to locate your files.",
        ).as_json_schema_extra(),
    )

    @field_validator("path", mode="before")
    def validate_storage_path(cls, value: str) -> str:  # noqa: N805
        if not value.startswith("storage:"):
            err_msg = "Storage path must have `storage:` schema"
            raise ValueError(err_msg)
        return value

    def is_absolute(self) -> bool:
        return self.path.startswith("storage://")

    def get_absolute_path_model(self, client: apolo_sdk.Client) -> "ApoloFilesPath":
        if self.is_absolute():
            return self

        volume = client.parse.volume(f"{self.path}:rw")
        return self.model_copy(update={"path": str(volume.storage_uri)})


class MountPath(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Mount Path",
            description="Specify the absolute path.",
        ).as_json_schema_extra(),
    )
    path: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Path",
            description="Specify the absolute path inside the "
            "container where the volume should be mounted.",
        ).as_json_schema_extra(),
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


class ApoloMountMode(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Files Mount",
            description="Configure how Apolo Files should be "
            "mounted into the application’s workload environment.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )

    mode: ApoloMountModes = Field(
        default=ApoloMountModes.RW,
        json_schema_extra=SchemaExtraMetadata(
            title="Mount Mode",
            description="Select the access mode for the mount,"
            " such as read-only or read-write.",
        ).as_json_schema_extra(),
    )


class ApoloFilesMount(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Files Mount",
            description="Configure Apolo Files mount within the application workloads.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    storage_uri: ApoloFilesPath
    mount_path: MountPath
    mode: ApoloMountMode = Field(
        default=ApoloMountMode(),
    )


class ApoloFilesFile(ApoloFilesPath): ...


class StorageMounts(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Mounts",
            description="Mount external storage paths",
        ).as_json_schema_extra(),
    )
    mounts: list[ApoloFilesMount] = Field(
        default_factory=list,
        description="List of ApoloStorageMount objects to mount external storage paths",
    )
