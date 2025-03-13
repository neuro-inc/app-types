from enum import Enum

from apolo_app_types import AppInputsDeployer
from apolo_app_types.protocols.common import AppOutputsDeployer


class JupyterTypes(str, Enum):
    LAB = "lab"
    NOTEBOOK = "notebook"


class JupyterInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True
    jupyter_type: JupyterTypes = JupyterTypes.LAB


class JupyterOutputs(AppOutputsDeployer):
    internal_web_app_url: str
