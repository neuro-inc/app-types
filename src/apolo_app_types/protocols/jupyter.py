from enum import Enum

from apolo_app_types.protocols.common import AppInputs, AppOutputs


class JupyterTypes(str, Enum):
    LAB = "lab"
    NOTEBOOK = "notebook"


class JupyterInputs(AppInputs):
    preset_name: str
    http_auth: bool = True
    jupyter_type: JupyterTypes = JupyterTypes.LAB


class JupyterOutputs(AppOutputs):
    internal_web_app_url: str
