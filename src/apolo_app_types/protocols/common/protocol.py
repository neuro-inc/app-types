from pydantic import BaseModel, ConfigDict


class Protocol(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())
