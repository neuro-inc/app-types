from pydantic import Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppInputsDeployer,
    AppOutputs,
    AppOutputsDeployer,
    BasicNetworkingConfig,
    Preset,
    SchemaExtraMetadata,
)


class ShellInputs(AppInputsDeployer):
    preset_name: str
    http_auth: bool = True


class ShellOutputs(AppOutputsDeployer):
    internal_web_app_url: str


class ShellAppInputs(AppInputs):
    preset: Preset
    networking: BasicNetworkingConfig = Field(
        default_factory=BasicNetworkingConfig,
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Settings",
            description="Configure network access, HTTP authentication,"
            " and related connectivity options.",
        ).as_json_schema_extra(),
    )


class ShellAppOutputs(AppOutputs):
    pass
