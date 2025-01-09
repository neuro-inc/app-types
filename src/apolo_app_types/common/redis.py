from pydantic import BaseModel
from apolo_app_types.common.preset import Preset


class RedisMaster(BaseModel):
    preset: Preset


class Redis(BaseModel):
    master: RedisMaster
