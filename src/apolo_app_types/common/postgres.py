from pydantic import BaseModel, Field


class Postgres(BaseModel):
    platform_app_name: str = Field(
        ...,
        description="The name of the Postgres platform app.",
        title="Platform app name"
    )
    username: str | None = Field(
        None,
        description="The username to access the Postgres database.",
        title="Postgres Username"
    )
    db_name: str | None = Field(
        None,
        description="The name of the Postgres database.",
        title="Postgres Database Name"
    )
