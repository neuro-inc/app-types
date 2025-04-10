from enum import Enum

from pydantic import ConfigDict, Field

from apolo_app_types import AppInputsDeployer, AppOutputs
from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputsDeployer,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.networking import RestAPI
from apolo_app_types.protocols.common.storage import ApoloFilesMount, StorageMounts


class JupyterTypes(str, Enum):
    LAB = "lab"
    NOTEBOOK = "notebook"


class JupyterInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True
    jupyter_type: JupyterTypes = JupyterTypes.LAB


class JupyterOutputs(AppOutputsDeployer):
    internal_web_app_url: str


class JupyterSpecificAppInputs(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Jupyter App",
            description="Jupyter App configuration.",
        ).as_json_schema_extra(),
    )
    jupyter_type: JupyterTypes = Field(
        default=JupyterTypes.LAB,
        description="Type of Jupyter application (lab or notebook).",
        title="Jupyter Type",
    )
    http_auth: bool = Field(
        default=True,
        description="Whether to use HTTP authentication.",
        title="HTTP Authentication",
    )
    code_storage_mount: ApoloFilesMount | None = Field(
        default=None,
        title="Code Storage Mount",
        description=(
            "Configure Apolo Files mount within the application workloads. "
            "If not set, Apolo will automatically assign a mount to the storage."
        ),
    )
    extra_storage_mounts: StorageMounts | None = None


class JupyterAppInputs(AppInputs):
    preset: Preset
    jupyter_specific: JupyterSpecificAppInputs


class JupyterAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI
    external_web_app_url: RestAPI
