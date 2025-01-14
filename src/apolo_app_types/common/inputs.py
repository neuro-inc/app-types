from pydantic import BaseModel, ConfigDict, SecretStr, Field


class AppInputs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    secrets: dict[str, SecretStr] = Field(default_factory=dict, description="Sensitive secrets")
