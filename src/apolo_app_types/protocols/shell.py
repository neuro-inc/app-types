from pydantic import Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppInputsDeployer,
    AppOutputs,
    AppOutputsDeployer,
    Preset,
    RestAPI,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.jupyter import Networking


class ShellInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class ShellOutputs(AppOutputsDeployer):
    internal_web_app_url: str


class ShellAppInputs(AppInputs):
    preset: Preset
    networking: Networking = Field(
        default=Networking(http_auth=True),
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Settings",
            description="Configure network access, HTTP authentication,"
            " and related connectivity options.",
        ).as_json_schema_extra(),
    )


class ShellAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI
    external_web_app_url: RestAPI
