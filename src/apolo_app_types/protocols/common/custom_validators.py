from collections.abc import Awaitable, Callable, Mapping
from numbers import Real
from typing import Any, TypedDict

PRESET_VALIDATOR_NAME = "preset_validator"


class PresetValidatorConfig(TypedDict, total=False):
    exists: bool
    min_cpu_cores: float
    min_ram_gib: int
    min_vram_gib: int


class CustomValidatorSpec(TypedDict, total=False):
    preset_validator: PresetValidatorConfig


class CustomValidationError(Exception):
    def __init__(self, message: str, path: list[str | int], validator: str):
        self.message = message
        self.path = list(path)
        self.validator = validator
        super().__init__(message)


def preset_validator(
    *,
    exists: bool | None = None,
    min_cpu_cores: float | None = None,
    min_ram_gib: int | None = None,
    min_vram_gib: int | None = None,
) -> CustomValidatorSpec:
    config: PresetValidatorConfig = {}
    if exists is not None:
        config["exists"] = exists
    if min_cpu_cores is not None:
        config["min_cpu_cores"] = min_cpu_cores
    if min_ram_gib is not None:
        config["min_ram_gib"] = min_ram_gib
    if min_vram_gib is not None:
        config["min_vram_gib"] = min_vram_gib
    return {"preset_validator": config}


def _get_preset_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        name = value.get("name")
        if isinstance(name, str):
            return name
    return None


def _get_preset_max_vram_bytes(preset: Any) -> int | None:
    vram_candidates: list[int] = []
    for gpu in (
        getattr(preset, "nvidia_gpu", None),
        getattr(preset, "amd_gpu", None),
        getattr(preset, "intel_gpu", None),
    ):
        memory = getattr(gpu, "memory", None)
        if isinstance(memory, int):
            vram_candidates.append(memory)
    nvidia_migs = getattr(preset, "nvidia_migs", None) or {}
    for mig in nvidia_migs.values():
        memory = getattr(mig, "memory", None)
        if isinstance(memory, int):
            vram_candidates.append(memory)
    if not vram_candidates:
        return None
    return max(vram_candidates)


def _get_preset_ram_bytes(preset: Any) -> int | None:
    memory = getattr(preset, "memory", None)
    if isinstance(memory, int):
        return memory
    return None


def _build_custom_validation_error(
    message: str, path: list[str | int], validator: str
) -> CustomValidationError:
    return CustomValidationError(message=message, path=path, validator=validator)


async def validate_preset_custom_validator(
    value: Any,
    validator_config: Mapping[str, Any],
    *,
    cluster_name: str,
    path: list[str | int],
    apolo_client: Any,
) -> list[CustomValidationError]:
    preset_name = _get_preset_name(value)
    if preset_name is None:
        return []

    presets = apolo_client.config.presets
    preset = presets.get(preset_name)
    errors: list[CustomValidationError] = []
    if validator_config.get("exists") is True and preset is None:
        errors.append(
            _build_custom_validation_error(
                (
                    f"Preset '{preset_name}' is not available on cluster "
                    f"'{cluster_name}'."
                ),
                path,
                PRESET_VALIDATOR_NAME,
            )
        )
        return errors

    min_cpu_cores = validator_config.get("min_cpu_cores")
    if isinstance(min_cpu_cores, Real) and preset is not None:
        if getattr(preset, "cpu", None) is None or float(preset.cpu) < float(
            min_cpu_cores
        ):
            errors.append(
                _build_custom_validation_error(
                    (
                        f"Preset '{preset_name}' must provide at least "
                        f"{min_cpu_cores} CPU cores on cluster "
                        f"'{cluster_name}'."
                    ),
                    path,
                    PRESET_VALIDATOR_NAME,
                )
            )

    min_ram_gib = validator_config.get("min_ram_gib")
    if isinstance(min_ram_gib, int) and preset is not None:
        required_ram_bytes = min_ram_gib * 2**30
        available_ram_bytes = _get_preset_ram_bytes(preset)
        if available_ram_bytes is None or available_ram_bytes < required_ram_bytes:
            errors.append(
                _build_custom_validation_error(
                    (
                        f"Preset '{preset_name}' must provide at least "
                        f"{min_ram_gib} GiB of RAM on cluster "
                        f"'{cluster_name}'."
                    ),
                    path,
                    PRESET_VALIDATOR_NAME,
                )
            )

    min_vram_gib = validator_config.get("min_vram_gib")
    if isinstance(min_vram_gib, int) and preset is not None:
        required_vram_bytes = min_vram_gib * 2**30
        available_vram_bytes = _get_preset_max_vram_bytes(preset)
        if available_vram_bytes is None or available_vram_bytes < required_vram_bytes:
            errors.append(
                _build_custom_validation_error(
                    (
                        f"Preset '{preset_name}' must provide at least "
                        f"{min_vram_gib} GiB of GPU memory on cluster "
                        f"'{cluster_name}'."
                    ),
                    path,
                    PRESET_VALIDATOR_NAME,
                )
            )
    return errors


CustomSchemaValidator = Callable[
    ...,
    Awaitable[list[CustomValidationError]],
]


CUSTOM_VALIDATORS: dict[str, CustomSchemaValidator] = {
    PRESET_VALIDATOR_NAME: validate_preset_custom_validator,
}
