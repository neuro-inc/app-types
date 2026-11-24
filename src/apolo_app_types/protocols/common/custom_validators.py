import asyncio
import logging
import re
import unicodedata
from collections.abc import Awaitable, Callable, Mapping
from numbers import Real
from typing import Any
from urllib.parse import unquote

from apolo_sdk import ResourceNotFound
from typing_extensions import TypedDict
from yarl import URL


logger = logging.getLogger(__name__)

PRESET_VALIDATOR_NAME = "preset_validator"
STORAGE_PATH_VALIDATOR_NAME = "storage_path_validator"
STORAGE_PATH_STAT_TIMEOUT_S = 30
STORAGE_PATH_PREFIX = "storage:"
ENCODED_SEPARATOR_RE = re.compile(r"%2[EeFf]")
CLUSTER_NAME_ERROR = (
    "has an invalid cluster name. "
    "Use storage://<cluster>/<org>/<project>/<folder> or storage:<folder>."
)
CLUSTER_LABEL_RE = re.compile(r"[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?")


class PresetValidatorConfig(TypedDict, total=False):
    exists: bool
    min_cpu_cores: float
    min_ram_gib: int
    min_vram_gib: int


class StoragePathValidatorConfig(TypedDict, total=False):
    exists: bool
    is_dir: bool
    same_project: bool
    subfolder: bool


class CustomValidatorSpec(TypedDict, total=False):
    preset_validator: PresetValidatorConfig
    storage_path_validator: StoragePathValidatorConfig


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


def storage_path_validator(
    *,
    exists: bool | None = None,
    is_dir: bool | None = None,
    same_project: bool | None = None,
    subfolder: bool | None = None,
) -> CustomValidatorSpec:
    if exists is False and is_dir is True:
        msg = "storage_path_validator cannot require a directory when exists=False."
        raise ValueError(msg)
    if subfolder is True and same_project is not True:
        msg = "storage_path_validator cannot require a subfolder without same_project."
        raise ValueError(msg)
    config: StoragePathValidatorConfig = {}
    if exists is not None:
        config["exists"] = exists
    if is_dir is not None:
        config["is_dir"] = is_dir
    if same_project is not None:
        config["same_project"] = same_project
    if subfolder is not None:
        config["subfolder"] = subfolder
    return {"storage_path_validator": config}


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


def _get_storage_path(value: Any) -> str | None:
    if not isinstance(value, Mapping):
        return None
    files_path = value.get("files_path")
    if not isinstance(files_path, Mapping):
        return None
    path = files_path.get("path")
    if isinstance(path, str):
        return path
    return None


def _has_control_characters(value: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in value)


def _is_cluster_name(name: str) -> bool:
    return all(CLUSTER_LABEL_RE.fullmatch(label) for label in name.split("."))


def _get_plain_storage_path_error(storage_path: str) -> str | None:
    if not storage_path.startswith(STORAGE_PATH_PREFIX):
        return (
            f"Storage path {storage_path!r} must start with "
            f"'{STORAGE_PATH_PREFIX}' in lower case, e.g. storage:models."
        )
    raw_rest = storage_path.removeprefix(STORAGE_PATH_PREFIX)
    try:
        rest = unquote(raw_rest, errors="strict")
    except UnicodeDecodeError:
        return (
            f"Storage path {storage_path!r} has a percent-encoded sequence that "
            "is not UTF-8 text. Encode the folder name as UTF-8."
        )
    if _has_control_characters(rest):
        return (
            f"Storage path {storage_path!r} has a control character, such as "
            "a line break or a tab. Remove it from the path."
        )
    if "%" in rest:
        return (
            f"Storage path {storage_path!r} has '%' after percent-decoding. "
            "Encode each character once, or rename the folder that has '%' "
            "in its name."
        )
    if ENCODED_SEPARATOR_RE.search(raw_rest):
        return (
            f"Storage path {storage_path!r} has a percent-encoded '/' or '.'. "
            "Write them as plain characters."
        )
    forbidden = "".join(char for char in ":?#" if char in rest)
    if forbidden:
        return (
            f"Storage path {storage_path!r} has {', '.join(map(repr, forbidden))} "
            f"after '{STORAGE_PATH_PREFIX}', also when percent-encoded. Remove it "
            "from the path, or rename the folder that has it in its name."
        )
    absolute = rest.startswith("//")
    segments = (rest[2:] if absolute else rest.removeprefix("/")).split("/")
    if "" in segments[:-1]:
        return (
            f"Storage path {storage_path!r} has an empty folder name. "
            "Remove the extra '/'."
        )
    if absolute and not _is_cluster_name(segments[0]):
        return f"Storage path {storage_path!r} {CLUSTER_NAME_ERROR}"
    return None


def _get_storage_path_location_error(
    storage_path: str,
    uri: URL,
    validator_config: Mapping[str, Any],
    config: Any,
) -> str | None:
    parts = tuple(part for part in uri.path.split("/") if part not in ("", "."))
    if validator_config.get("same_project") is True and (
        uri.host != config.cluster_name
        or parts[:2] != (config.org_name, config.project_name)
        or ".." in parts
    ):
        return (
            f"Storage path '{storage_path}' must be in project "
            f"'{config.project_name}' of organization "
            f"'{config.org_name}' on cluster '{config.cluster_name}'."
        )
    subfolder = validator_config.get("subfolder", validator_config.get("same_project"))
    if subfolder is True and len(parts) <= 2:
        return (
            f"Storage path '{storage_path}' is the root of a project. "
            "Choose a subfolder of the project, e.g. storage:models."
        )
    return None


async def validate_storage_path_custom_validator(
    value: Any,
    validator_config: Mapping[str, Any],
    *,
    cluster_name: str,
    path: list[str | int],
    apolo_client: Any,
) -> list[CustomValidationError]:
    storage_path = _get_storage_path(value)
    if storage_path is None:
        return []

    plain_error = _get_plain_storage_path_error(storage_path)
    if plain_error is not None:
        return [
            _build_custom_validation_error(
                plain_error, path, STORAGE_PATH_VALIDATOR_NAME
            )
        ]

    try:
        uri: URL = apolo_client.parse.str_to_uri(
            storage_path, allowed_schemes=("storage",)
        )
    except UnicodeError:
        return [
            _build_custom_validation_error(
                f"Storage path {storage_path!r} {CLUSTER_NAME_ERROR}",
                path,
                STORAGE_PATH_VALIDATOR_NAME,
            )
        ]
    except ValueError as e:
        return [
            _build_custom_validation_error(
                f"Storage path '{storage_path}' is invalid: {e}",
                path,
                STORAGE_PATH_VALIDATOR_NAME,
            )
        ]

    location_error = _get_storage_path_location_error(
        storage_path, uri, validator_config, apolo_client.config
    )
    if location_error is not None:
        return [
            _build_custom_validation_error(
                location_error, path, STORAGE_PATH_VALIDATOR_NAME
            )
        ]

    is_dir = validator_config.get("is_dir") is True
    if validator_config.get("exists") is not True and not is_dir:
        return []

    try:
        async with asyncio.timeout(STORAGE_PATH_STAT_TIMEOUT_S):
            status = await apolo_client.storage.stat(uri)
    except ResourceNotFound:
        return [
            _build_custom_validation_error(
                f"Storage path '{storage_path}' does not exist or is not accessible.",
                path,
                STORAGE_PATH_VALIDATOR_NAME,
            )
        ]
    except Exception:
        logger.warning("Failed to stat storage path %s", uri, exc_info=True)
        return [
            _build_custom_validation_error(
                f"Storage path '{storage_path}' could not be checked, "
                "please try again later.",
                path,
                STORAGE_PATH_VALIDATOR_NAME,
            )
        ]
    if is_dir and not status.is_dir():
        return [
            _build_custom_validation_error(
                f"Storage path '{storage_path}' is not a directory.",
                path,
                STORAGE_PATH_VALIDATOR_NAME,
            )
        ]
    return []


CustomSchemaValidator = Callable[
    ...,
    Awaitable[list[CustomValidationError]],
]


CUSTOM_VALIDATORS: dict[str, CustomSchemaValidator] = {
    PRESET_VALIDATOR_NAME: validate_preset_custom_validator,
    STORAGE_PATH_VALIDATOR_NAME: validate_storage_path_custom_validator,
}
