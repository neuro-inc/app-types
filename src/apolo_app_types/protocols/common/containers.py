from pydantic import BaseModel


class ContainerImage(BaseModel):
    repository: str
    tag: str | None = None
