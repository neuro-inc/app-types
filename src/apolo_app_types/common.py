from pydantic import BaseModel, ConfigDict


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AppOutputs(BaseModel):
    external_web_app_url: str | None = None
