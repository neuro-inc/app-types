from pydantic import BaseModel


class BasicAuth(BaseModel):
    username: str = ""
    password: str = ""
