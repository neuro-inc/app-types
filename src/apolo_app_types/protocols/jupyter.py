from enum import Enum

from pydantic import ConfigDict, Field

from apolo_app_types import AppInputsDeployer, AppOutputs
from apolo_app_types.helm.utils.storage import get_app_data_files_relative_path_url
from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputsDeployer,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.networking import RestAPI
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    StorageMounts,
)
from apolo_app_types.protocols.mlflow import MLFlowTrackingServerURL


_JUPYTER_DEFAULTS = {
    "storage": str(
        get_app_data_files_relative_path_url(
            app_type_name="jupyter", app_name="jupyter-app"
        )
        / "code"
    ),
    "mount": "/root/notebooks",
}


class JupyterTypes(str, Enum):
    LAB = "lab"
    NOTEBOOK = "notebook"


class JupyterInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True
    jupyter_type: JupyterTypes = JupyterTypes.LAB


class JupyterOutputs(AppOutputsDeployer):
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
        description="Whether to use HTTP authentication.",
        title="HTTP Authentication",
    )


class JupyterSpecificAppInputs(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Jupyter App",
            description="Configure the Jupyter App.",
        ).as_json_schema_extra(),
    )
    jupyter_type: JupyterTypes = Field(
        default=JupyterTypes.LAB,
        description=(
            "Choose whether the Jupyter server should run in 'lab' or 'notebook' mode."
        ),
        title="Jupyter server type",
    )
    override_code_storage_mount: ApoloFilesMount | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Override Default Storage Mount",
            description=(
                "Override Apolo Files mount within the application workloads. "
                "If not set, Apolo will automatically mount "
                f'"{_JUPYTER_DEFAULTS["storage"]}" to "{_JUPYTER_DEFAULTS["mount"]}"'
            ),
        ).as_json_schema_extra(),
    )


class JupyterAppInputs(AppInputs):
    preset: Preset

    jupyter_specific: JupyterSpecificAppInputs

    extra_storage_mounts: StorageMounts | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Extra Storage Mounts",
            description="Attach additional storage volumes to the Jupyter application.",
        ).as_json_schema_extra(),
    )

    networking: Networking = Field(
        default=Networking(http_auth=True),
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Settings",
            description="Configure network access, HTTP authentication,"
            " and related connectivity options.",
        ).as_json_schema_extra(),
    )

    mlflow_integration: MLFlowTrackingServerURL | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Integration",
            description="Enable integration with MLFlow for"
            " experiment tracking and model management.",
        ).as_json_schema_extra(),
    )


class JupyterAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI
    external_web_app_url: RestAPI
