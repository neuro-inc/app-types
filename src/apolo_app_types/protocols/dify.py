from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    AppOutputs,
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.networking import RestAPI, ServiceAPI


class DifySpecificOutputs(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify Specific Outputs",
            description="Configure Dify Specific Outputs.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    init_password: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Init Password",
            description="The initial password for the Dify application.",
        ).as_json_schema_extra(),
    )


class DifyAppOutputs(AppOutputs):
    api_url: ServiceAPI[RestAPI] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="API URL",
            description="The URL of the API.",
        ).as_json_schema_extra(),
    )
    dify_specific: DifySpecificOutputs
