from pydantic import BaseModel, ConfigDict


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AppOutputs(BaseModel):
    pass
