from pydantic import ConfigDict, Field

from apolo_app_types import AppInputs, AppOutputs
from apolo_app_types.helm.utils.storage import get_app_data_files_relative_path_url
from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.networking import RestAPI
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    ApoloMountModes,
    MountPath,
    StorageMounts,
)
from apolo_app_types.protocols.mlflow import MLFlowAppOutputs


class VSCodeInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class VSCodeOutputs(AppOutputsDeployer):
    internal_web_app_url: str


def _get_app_data_files_path_url() -> str:
    # Passing app_type_name as string to avoid circular import
    return str(
        get_app_data_files_relative_path_url(
            app_type_name="vscode", app_name="vscode-app"
        )
        / "code"
    )


class Networking(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Settings",
            description="Network settings",
        ).as_json_schema_extra(),
    )
    http_auth: bool = Field(
        default=True,
        json_schema_extra=SchemaExtraMetadata(
            description="Whether to use HTTP authentication.",
            title="HTTP Authentication",
        ).as_json_schema_extra(),
    )


class VSCodeMainStoragePath(ApoloFilesPath):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Code Storage Path",
            description="This is the path in Apolo Storage that will be"
            " mounted in the container.",
        ).as_json_schema_extra(),
    )
    path: str = Field(
        default=_get_app_data_files_path_url(),
        json_schema_extra=SchemaExtraMetadata(
            title="Apolo Path",
            description="This path always starts with `storage:`. "
            "You can use a relative path like `storage:directory` "
            "(which maps to the current project) or an absolute path "
            "like `storage://cluster/org/proj/directory`.",
        ).as_json_schema_extra(),
    )


class VSCodeMainMountPath(MountPath):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Code Mount Path",
            description="This is the path in the container where the code storage "
            "will be mounted.",
        ).as_json_schema_extra(),
    )
    path: str = Field(
        default="/home/coder/project",
        json_schema_extra=SchemaExtraMetadata(
            title="Mount Path",
            description="Linux-style path inside the container where the volume "
            "will be mounted.",
        ).as_json_schema_extra(),
    )


class VSCodeFilesMount(ApoloFilesMount):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Code Storage Mount",
            description="Code storage mount for VSCode.",
        ).as_json_schema_extra(),
    )
    storage_uri: VSCodeMainStoragePath = Field(default=VSCodeMainStoragePath())
    mount_path: VSCodeMainMountPath = Field(default=VSCodeMainMountPath())
    mode: ApoloMountMode = Field(
        default=ApoloMountMode(mode=ApoloMountModes.RW),
        json_schema_extra=SchemaExtraMetadata(
            title="Mount Mode",
            description="Mount mode for the code storage.",
        ).as_json_schema_extra(),
    )


class VSCodeSpecificAppInputs(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="VSCode App",
            description="VSCode App configuration.",
        ).as_json_schema_extra(),
    )
    code_storage_mount: VSCodeFilesMount = Field(default=VSCodeFilesMount())


class VSCodeAppInputs(AppInputs):
    preset: Preset
    vscode_specific: VSCodeSpecificAppInputs
    extra_storage_mounts: StorageMounts | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Extra Storage Mounts",
            description=("Additional storage mounts for the application."),
        ).as_json_schema_extra(),
    )
    networking: Networking = Field(
        default=Networking(http_auth=True),
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Settings",
            description=("Network settings for the application."),
        ).as_json_schema_extra(),
    )
    mlflow_integration: MLFlowAppOutputs | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Integration",
            description=(
                "MLFlow integration settings for the application. "
                "If not set, MLFlow integration will not be enabled."
            ),
        ).as_json_schema_extra(),
    )


class VSCodeAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI
    external_web_app_url: RestAPI
