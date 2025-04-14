import enum
import re

from pydantic import ConfigDict, Field, computed_field, field_validator

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)


class StorageGB(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Storage",
            description="Storage configuration.",
        ).as_json_schema_extra(),
    )
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


class ApoloFilesPath(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Files path",
            description="Path within Apolo Files application to use.",
        ).as_json_schema_extra(),
    )
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


class ApoloFilesRelativePath(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Files path",
            description="Path within Apolo Files application to use.",
        ).as_json_schema_extra(),
    )
    relative_path: str = Field(
        ...,
        description="The path to the Apolo Storage.",
        title="Storage path",
    )

    @computed_field  # type: ignore
    @property
    def path_parts(self) -> tuple[None | str, str]:
        full_path = self.relative_path.replace("storage:", "")
        if full_path.startswith("/"):
            project, path = full_path[1:].split("/", maxsplit=1)
            return project, path
        return None, full_path

    def get_absolute_path(
        self, org: str, cluster: str, project: str | None
    ) -> ApoloFilesPath:
        project_part, path = self.path_parts
        project_part = project_part or project

        if not project_part:
            err_msg = "Project is not set."
            raise ValueError(err_msg)

        return ApoloFilesPath(path=f"storage://{cluster}/{org}/{project_part}/{path}")

    @field_validator("relative_path", mode="before")
    def validate_storage_path(cls, value: str) -> str:  # noqa: N805
        if not re.match(r"storage:(?!//)", value):
            err_msg = (
                "Storage path must have `storage:` schema and be of absolute path."
            )
            raise ValueError(err_msg)
        return value


class MountPath(AbstractAppFieldType):
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


class ApoloMountMode(AbstractAppFieldType):
    mode: ApoloMountModes = Field(
        default=ApoloMountModes.RW,
        description="The mode of the mount.",
        title="Mount mode",
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
    storage_uri: ApoloFilesPath | ApoloFilesRelativePath = Field(
        ...,
        description="The path to the Apolo Files.",
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
