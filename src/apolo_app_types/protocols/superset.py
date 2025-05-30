from pydantic import Field

from apolo_app_types.protocols.common import (
    AppInputs,
    AppOutputs,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
    ServiceAPI,
)
from apolo_app_types.protocols.common.networking import HttpApi


class SupersetInputs(AppInputs):
    ingress_http: IngressHttp
    preset: Preset


class SupersetOutputs(AppOutputs):
    web_app_url: ServiceAPI[HttpApi] = Field(
        default=ServiceAPI[HttpApi](),
        json_schema_extra=SchemaExtraMetadata(
            title="Superset Web App URL",
            description=("URL to access the Superset web application. "),
        ).as_json_schema_extra(),
    )
