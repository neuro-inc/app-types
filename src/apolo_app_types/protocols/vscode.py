from pydantic import ConfigDict, Field

from apolo_app_types import AppInputs, AppOutputs
from apolo_app_types.helm.utils.storage import get_app_data_files_relative_path_url
from apolo_app_types.protocols.common import AppInputsDeployer, AppOutputsDeployer
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.networking import RestAPI
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    StorageMounts,
)
from apolo_app_types.protocols.mlflow import MLFlowTrackingServerURL


_VSCODE_DEFAULTS = {
    "storage": str(
        get_app_data_files_relative_path_url(
            app_type_name="vscode", app_name="vscode-app"
        )
        / "code"
    ),
    "mount": "/home/coder/project",
}


class VSCodeInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class VSCodeOutputs(AppOutputsDeployer):
    internal_web_app_url: str


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


class VSCodeSpecificAppInputs(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="VSCode App",
            description="VSCode App configuration.",
        ).as_json_schema_extra(),
    )
    override_code_storage_mount: ApoloFilesMount | None = Field(
        None,
        json_schema_extra=SchemaExtraMetadata(
            title="Override Default Storage Mounts",
            description=(
                "Override Apolo Files mount within the application workloads. "
                "If not set, Apolo will automatically mount "
                f'"{_VSCODE_DEFAULTS["storage"]}" to "{_VSCODE_DEFAULTS["mount"]}"'
            ),
        ).as_json_schema_extra(),
    )


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
    mlflow_integration: MLFlowTrackingServerURL | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Integration",
            description=(
                "MLFlow integration settings for the application. "
                "If not set, MLFlow integration will not be enabled."
            ),
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )


class VSCodeAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI
    external_web_app_url: RestAPI
