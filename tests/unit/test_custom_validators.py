import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from apolo_sdk import (
    Action,
    AuthorizationError,
    FileStatus,
    FileStatusType,
    ResourceNotFound,
    ServerNotAvailable,
)
from apolo_sdk._url_utils import uri_from_cli
from yarl import URL

from apolo_app_types.protocols.common import custom_validators
from apolo_app_types.protocols.common.custom_validators import (
    CUSTOM_VALIDATORS,
    PRESET_VALIDATOR_NAME,
    STORAGE_PATH_VALIDATOR_NAME,
    CustomValidationError,
    validate_preset_custom_validator,
    validate_storage_path_custom_validator,
)


def _make_client(preset: object | None) -> MagicMock:
    client = MagicMock()
    client.config.presets = {"preset-a": preset}
    return client


def _gpu_preset(*, memory: int | None = None) -> SimpleNamespace:
    return SimpleNamespace(memory=memory)


def test_validate_preset_custom_validator_reports_missing_preset() -> None:
    errors = asyncio.run(
        validate_preset_custom_validator(
            {"name": "preset-a"},
            {"exists": True},
            cluster_name="test-cluster",
            path=["preset"],
            apolo_client=_make_client(None),
        )
    )

    assert len(errors) == 1
    assert isinstance(errors[0], CustomValidationError)
    assert errors[0].validator == "preset_validator"


@pytest.mark.parametrize(
    ("preset", "validator_config", "expected_message_part"),
    [
        (
            SimpleNamespace(
                cpu=2.0,
                memory=8 * (1 << 30),
                nvidia_gpu=None,
                amd_gpu=None,
                intel_gpu=None,
                nvidia_migs={},
            ),
            {"min_cpu_cores": 4},
            "CPU cores",
        ),
        (
            SimpleNamespace(
                cpu=4.0,
                memory=4 * (1 << 30),
                nvidia_gpu=None,
                amd_gpu=None,
                intel_gpu=None,
                nvidia_migs={},
            ),
            {"min_ram_gib": 8},
            "RAM",
        ),
        (
            SimpleNamespace(
                cpu=4.0,
                memory=8 * (1 << 30),
                nvidia_gpu=_gpu_preset(memory=8 * (1 << 30)),
                amd_gpu=None,
                intel_gpu=None,
                nvidia_migs={},
            ),
            {
                "min_vram_gib": 10,
                "exists": True,
            },
            "GPU memory",
        ),
    ],
)
def test_validate_preset_custom_validator_reports_resource_mismatch(
    preset: object,
    validator_config: dict[str, object],
    expected_message_part: str,
) -> None:
    errors = asyncio.run(
        validate_preset_custom_validator(
            {"name": "preset-a"},
            validator_config,
            cluster_name="test-cluster",
            path=["preset"],
            apolo_client=_make_client(preset),
        )
    )

    assert errors
    assert any(expected_message_part in error.message for error in errors)


def test_validate_preset_custom_validator_accepts_matching_preset() -> None:
    errors = asyncio.run(
        validate_preset_custom_validator(
            {"name": "preset-a"},
            {
                "exists": True,
                "min_cpu_cores": 2,
                "min_ram_gib": 4,
                "min_vram_gib": 2,
            },
            cluster_name="test-cluster",
            path=["preset"],
            apolo_client=_make_client(
                SimpleNamespace(
                    cpu=4.0,
                    memory=8 * (1 << 30),
                    amd_gpu=None,
                    intel_gpu=None,
                    nvidia_gpu=SimpleNamespace(memory=2 * (1 << 30)),
                    nvidia_migs={},
                )
            ),
        )
    )

    assert errors == []


def test_custom_validators_registry_exposes_validators() -> None:
    assert CUSTOM_VALIDATORS == {
        PRESET_VALIDATOR_NAME: validate_preset_custom_validator,
        STORAGE_PATH_VALIDATOR_NAME: validate_storage_path_custom_validator,
    }


STORAGE_VALIDATOR_CONFIG = {"exists": True, "is_dir": True, "same_project": True}


def _file_status(file_type: FileStatusType) -> FileStatus:
    return FileStatus(
        path="models",
        size=0,
        type=file_type,
        modification_time=0,
        permission=Action.READ,
        uri=URL("storage://cluster/test-org/test-project/models"),
    )


def _make_storage_client(
    *,
    stat_result: FileStatus | None = None,
    stat_error: Exception | None = None,
) -> MagicMock:
    client = MagicMock()
    client.config.cluster_name = "cluster"
    client.config.org_name = "test-org"
    client.config.project_name = "test-project"
    client.parse.str_to_uri = MagicMock(
        side_effect=lambda path, *, allowed_schemes: uri_from_cli(
            path,
            "test-project",
            "cluster",
            "test-org",
            allowed_schemes=allowed_schemes,
        )
    )
    client.storage.stat = AsyncMock(
        return_value=stat_result or _file_status(FileStatusType.DIRECTORY),
        side_effect=stat_error,
    )
    return client


def _validate_storage_path(
    value: Any,
    client: MagicMock,
    validator_config: dict[str, bool] = STORAGE_VALIDATOR_CONFIG,
) -> list[CustomValidationError]:
    return asyncio.run(
        validate_storage_path_custom_validator(
            value,
            validator_config,
            cluster_name="cluster",
            path=["model_repository"],
            apolo_client=client,
        )
    )


@pytest.mark.parametrize(
    ("storage_path", "expected_uri"),
    [
        ("storage:models", "storage://cluster/test-org/test-project/models"),
        ("storage:models/", "storage://cluster/test-org/test-project/models/"),
        (
            "storage://cluster/test-org/test-project/triton/models",
            "storage://cluster/test-org/test-project/triton/models",
        ),
    ],
)
def test_validate_storage_path_accepts_directory_in_project(
    storage_path: str, expected_uri: str
) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert errors == []
    client.storage.stat.assert_awaited_once_with(URL(expected_uri))


@pytest.mark.parametrize(
    "storage_path",
    [
        "storage:/other-project/models",
        "storage://cluster/test-org/other-project/models",
        "storage://cluster/other-org/test-project/models",
        "storage://other-cluster/test-org/test-project/models",
        "storage://cluster/test-org",
    ],
)
def test_validate_storage_path_rejects_path_outside_project(storage_path: str) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert len(errors) == 1
    assert errors[0].validator == STORAGE_PATH_VALIDATOR_NAME
    assert errors[0].path == ["model_repository"]
    assert "must be in project 'test-project'" in errors[0].message
    client.storage.stat.assert_not_awaited()


def test_validate_storage_path_reports_missing_path() -> None:
    client = _make_storage_client(stat_error=ResourceNotFound("404: Not Found"))

    errors = _validate_storage_path({"files_path": {"path": "storage:missing"}}, client)

    assert len(errors) == 1
    assert errors[0].message == (
        "Storage path 'storage:missing' does not exist or is not accessible."
    )


@pytest.mark.parametrize("file_type", [FileStatusType.FILE, FileStatusType.SYMLINK])
def test_validate_storage_path_reports_non_directory(
    file_type: FileStatusType,
) -> None:
    client = _make_storage_client(stat_result=_file_status(file_type))

    errors = _validate_storage_path({"files_path": {"path": "storage:models"}}, client)

    assert len(errors) == 1
    assert errors[0].message == "Storage path 'storage:models' is not a directory."


def test_validate_storage_path_allows_file_when_only_existence_required() -> None:
    client = _make_storage_client(stat_result=_file_status(FileStatusType.FILE))

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:models"}}, client, {"exists": True}
    )

    assert errors == []


@pytest.mark.parametrize(
    "stat_error",
    [
        AuthorizationError("403: Forbidden"),
        ServerNotAvailable("503: Service Unavailable"),
        OSError(5, "Input/output error"),
        TimeoutError(),
        aiohttp.ServerDisconnectedError(),
        KeyError("FileStatus"),
    ],
)
def test_validate_storage_path_reports_unchecked_path_on_stat_failure(
    stat_error: Exception,
) -> None:
    client = _make_storage_client(stat_error=stat_error)

    errors = _validate_storage_path({"files_path": {"path": "storage:models"}}, client)

    assert len(errors) == 1
    assert errors[0].message == (
        "Storage path 'storage:models' could not be checked, please try again later."
    )


def test_validate_storage_path_stops_waiting_for_stat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(custom_validators, "STORAGE_PATH_STAT_TIMEOUT_S", 0.1)

    async def stat_forever(uri: URL) -> FileStatus:
        await asyncio.Event().wait()
        return _file_status(FileStatusType.DIRECTORY)

    client = _make_storage_client()
    client.storage.stat = stat_forever

    errors = asyncio.run(
        asyncio.wait_for(
            validate_storage_path_custom_validator(
                {"files_path": {"path": "storage:models"}},
                STORAGE_VALIDATOR_CONFIG,
                cluster_name="cluster",
                path=["model_repository"],
                apolo_client=client,
            ),
            timeout=5,
        )
    )

    assert len(errors) == 1
    assert errors[0].message == (
        "Storage path 'storage:models' could not be checked, please try again later."
    )


@pytest.mark.parametrize("storage_path", ["s3://bucket/models", "storage:~/models"])
def test_validate_storage_path_reports_invalid_path(storage_path: str) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert len(errors) == 1
    assert errors[0].message.startswith(f"Storage path '{storage_path}' is invalid")
    client.storage.stat.assert_not_awaited()


def test_validate_storage_path_skips_stat_without_existence_checks() -> None:
    client = _make_storage_client()

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:models"}}, client, {"same_project": True}
    )

    assert errors == []
    client.storage.stat.assert_not_awaited()


@pytest.mark.parametrize(
    "value",
    [None, "storage:models", {}, {"files_path": None}, {"files_path": {"path": 1}}],
)
def test_validate_storage_path_ignores_values_without_path(value: Any) -> None:
    client = _make_storage_client()

    assert _validate_storage_path(value, client) == []
    client.storage.stat.assert_not_awaited()
