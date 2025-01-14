from pydantic import BaseModel, Field


class BasicAuth(BaseModel):
    username: str = Field(
        default="",
        description="The username for basic authentication.",
        title="Username",
    )
    password: str = Field(
        default="",
        description="The password for basic authentication.",
        title="Password",
    )
