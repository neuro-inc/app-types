from typing import TypedDict


PRESET_VALIDATOR_NAME = "preset_validator"


class PresetValidatorConfig(TypedDict, total=False):
    exists: bool
    min_vram_gb: int


class CustomValidatorSpec(TypedDict, total=False):
    preset_validator: PresetValidatorConfig


def preset_validator(
    *,
    exists: bool | None = None,
    min_vram_gb: int | None = None,
) -> CustomValidatorSpec:
    config: PresetValidatorConfig = {}
    if exists is not None:
        config["exists"] = exists
    if min_vram_gb is not None:
        config["min_vram_gb"] = min_vram_gb
    return {"preset_validator": config}
