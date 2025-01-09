from pydantic import BaseModel, Field, ConfigDict


class AppOutputs(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=()
    )

    external_web_app_url: str = Field(
        default=None,
        description="The URL of the external web app.",
        title="External web app URL"
    )

