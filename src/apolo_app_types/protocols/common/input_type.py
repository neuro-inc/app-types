from pydantic import BaseModel, ConfigDict


class InputType(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())