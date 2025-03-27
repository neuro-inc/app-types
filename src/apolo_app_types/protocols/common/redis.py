from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType


class RedisMaster(AbstractAppFieldType):
    preset_name: str  # todo: switch to src/apolo_app_types/protocols/common/preset.py


class Redis(AbstractAppFieldType):
    master: RedisMaster
