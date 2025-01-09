from pydantic import BaseModel


class RedisMaster(BaseModel):
    preset_name: str


class Redis(BaseModel):
    master: RedisMaster
