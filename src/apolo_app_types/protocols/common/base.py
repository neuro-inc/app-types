from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common.networking import ServiceAPI, WebApp


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class AppOutputs(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    app_url: ServiceAPI[WebApp] | None = Field(
        default=None,
        description="The main application URL for accessing the service. "
        "This is the primary endpoint users should use to access the application.",
        title="Application URL",
    )
