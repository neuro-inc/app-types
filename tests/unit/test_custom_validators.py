import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import MethodType, SimpleNamespace
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
    Storage,
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


STORAGE_VALIDATOR_CONFIG = {
    "exists": True,
    "is_dir": True,
    "same_project": True,
    "subfolder": True,
}


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
        (
            "storage:/test-project/models",
            "storage://cluster/test-org/test-project/models",
        ),
        ("storage:.models", "storage://cluster/test-org/test-project/.models"),
        ("storage:a..b", "storage://cluster/test-org/test-project/a..b"),
        ("storage:./models", "storage://cluster/test-org/test-project/models"),
        ("storage:моделі", "storage://cluster/test-org/test-project/моделі"),
        ("storage:my%20models", "storage://cluster/test-org/test-project/my%20models"),
        ("storage:user@models", "storage://cluster/test-org/test-project/user@models"),
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
        "storage://cluster/test-org/test-project/../other-project/models",
        "storage:..",
        "storage:../other-project/models",
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


@pytest.mark.parametrize(
    "storage_path",
    [
        "storage:",
        "storage:.",
        "storage:./",
        "storage:/test-project",
        "storage:/test-project/",
        "storage://cluster/test-org/test-project",
        "storage://cluster/test-org/test-project/",
        "storage://cluster/test-org/test-project/.",
        "storage://cluster/test-org/test-project/./",
        "storage:models/..",
        "storage:models/../",
        "storage://cluster/test-org/test-project/models/..",
    ],
)
def test_validate_storage_path_rejects_project_root(storage_path: str) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert len(errors) == 1
    assert errors[0].validator == STORAGE_PATH_VALIDATOR_NAME
    assert errors[0].path == ["model_repository"]
    assert errors[0].message == (
        f"Storage path '{storage_path}' is the root of a project. "
        "Choose a subfolder of the project, e.g. storage:models."
    )
    client.storage.stat.assert_not_awaited()


def test_validate_storage_path_allows_project_root_without_subfolder() -> None:
    client = _make_storage_client()

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:"}},
        client,
        {"exists": True, "is_dir": True, "same_project": True},
    )

    assert errors == []
    client.storage.stat.assert_awaited_once_with(
        URL("storage://cluster/test-org/test-project")
    )


def test_validate_storage_path_rejects_other_project_root_with_subfolder_only() -> None:
    client = _make_storage_client()

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:/other-project"}},
        client,
        {"subfolder": True},
    )

    assert len(errors) == 1
    assert "is the root of a project" in errors[0].message


PREFIX_ERROR = "must start with 'storage:' in lower case, e.g. storage:models."
CONTROL_ERROR = (
    "has a control character, such as a line break or a tab. Remove it from the path."
)
PERCENT_ERROR = (
    "has '%' after percent-decoding. Encode each character once, "
    "or rename the folder that has '%' in its name."
)
SEPARATOR_ERROR = "has a percent-encoded '/' or '.'. Write them as plain characters."
EMPTY_ERROR = "has an empty folder name. Remove the extra '/'."
CLUSTER_ERROR = (
    "has an invalid cluster name. "
    "Use storage://<cluster>/<org>/<project>/<folder> or storage:<folder>."
)


def _character_error(characters: str) -> str:
    return (
        f"has {characters} after 'storage:', also when percent-encoded. "
        "Remove it from the path, or rename the folder that has it in its name."
    )


UNSAFE_STORAGE_PATHS = [
    *(
        (storage_path, PREFIX_ERROR)
        for storage_path in [
            "",
            "s3://bucket/models",
            "STORAGE:models",
            "Storage:models",
            " storage:models",
        ]
    ),
    *(
        (storage_path, CONTROL_ERROR)
        for storage_path in [
            "storage:models\n",
            "storage:mod\nels",
            "storage:mod\tels",
            "storage:models\r",
            "storage:models\x00",
            "storage:models\x7f",
            "storage:models\x85",
            "storage:models%0a",
            "storage:models%00",
            "storage://cluster/test-org/test-project/a%7Fb",
            "storage://cluster/test-org/test-project/a%C2%85b",
            "storage:%0a/../models",
            "storage:%00/../models",
            "storage:models/%C2%85/..",
        ]
    ),
    *(
        (storage_path, PERCENT_ERROR)
        for storage_path in [
            "storage:models%25",
            "storage:100%",
            "storage:report%253A2026",
            "storage://cluster/test-org/test-project/%252e",
            "storage://cluster/test-org/test-project/%252e%252e/%252e%252e/other",
        ]
    ),
    *(
        (storage_path, SEPARATOR_ERROR)
        for storage_path in [
            "storage:triton%2Fmodels",
            "storage:%2e%2e/other-project/models",
            "storage://cluster/test-org/test-project/%2e",
            "storage://cluster/test-org/test-project%2F.",
            "storage://cluster/test-org/test-project%2F%2e",
            "storage://cluster/test-org/test-project/.%2F.",
            "storage://cluster/test-org/test-project%2F.%2F.",
            "storage://cluster/test-org/test-project/..%2fother-project/models",
        ]
    ),
    *(
        (storage_path, _character_error("':'"))
        for storage_path in [
            "storage:STORAGE:models",
            "storage:storage:models",
            "storage:storage://cluster/test-org/test-project/models",
            "storage:models/storage:x",
            "storage:models/v1:latest",
            "storage://cluster/test-org/test-project/storage:models",
            "storage:models%3Ax",
            "storage:/test-project/storage%3A/other",
            "storage:%3A/../models",
            "storage:%3a/../models",
            "storage:report:2026",
            "storage:report%3A2026",
            "storage://cluster:1/test-org/test-project/models",
            "storage://cluster:/test-org/test-project/models",
            "storage://cluster%3A/test-org/test-project/models",
        ]
    ),
    ("storage:models?x=1", _character_error("'?'")),
    ("storage:models%3Fx", _character_error("'?'")),
    ("storage:models#x", _character_error("'#'")),
    ("storage:models%23x", _character_error("'#'")),
    ("storage:a:b?c#d", _character_error("':', '?', '#'")),
    *(
        (storage_path, EMPTY_ERROR)
        for storage_path in [
            "storage://cluster//test-org/test-project/models",
            "storage:////test-project/models",
            "storage:///test-org/test-project/models",
            "storage://cluster/test-org/test-project//",
            "storage:/test-project//models",
            "storage:triton//models",
            "storage://cluster/test-org/test-project/./triton//models/",
        ]
    ),
    *(
        (storage_path, CLUSTER_ERROR)
        for storage_path in [
            "storage://",
            "storage://[",
            "storage://[cluster]/test-org/test-project/models",
            "storage://xn--/test-org/test-project/models",
            "storage://xn--abc/test-org/test-project/models",
            "storage://-cluster/test-org/test-project/models",
            "storage://user@cluster/test-org/test-project/models",
            "storage://cluster%40x/test-org/test-project/models",
            "storage://кластер/test-org/test-project/models",
        ]
    ),
]


@pytest.mark.parametrize(("storage_path", "expected"), UNSAFE_STORAGE_PATHS)
def test_validate_storage_path_rejects_unsafe_path(
    storage_path: str, expected: str
) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert len(errors) == 1
    assert errors[0].validator == STORAGE_PATH_VALIDATOR_NAME
    assert errors[0].path == ["model_repository"]
    assert errors[0].message == f"Storage path {storage_path!r} {expected}"
    client.storage.stat.assert_not_awaited()


@pytest.mark.parametrize(
    "validator_config",
    [{}, {"exists": True}, {"same_project": True}],
)
def test_validate_storage_path_rejects_unsafe_path_with_any_config(
    validator_config: dict[str, bool],
) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:mod\nels"}}, client, validator_config
    )

    assert len(errors) == 1
    assert CONTROL_ERROR in errors[0].message
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


def test_validate_storage_path_checks_directory_without_exists() -> None:
    client = _make_storage_client(stat_result=_file_status(FileStatusType.FILE))

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:models"}}, client, {"is_dir": True}
    )

    assert len(errors) == 1
    assert errors[0].message == "Storage path 'storage:models' is not a directory."


def test_validate_storage_path_allows_other_project_without_same_project() -> None:
    client = _make_storage_client()

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:/other-project/models"}},
        client,
        {"exists": True, "is_dir": True},
    )

    assert errors == []
    client.storage.stat.assert_awaited_once_with(
        URL("storage://cluster/test-org/other-project/models")
    )


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
    stat_error: Exception, caplog: pytest.LogCaptureFixture
) -> None:
    client = _make_storage_client(stat_error=stat_error)

    with caplog.at_level(logging.WARNING):
        errors = _validate_storage_path(
            {"files_path": {"path": "storage:models"}}, client
        )

    assert caplog.records[-1].exc_info is not None
    assert caplog.records[-1].exc_info[1] is stat_error

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


@pytest.mark.parametrize(
    "storage_path",
    ["storage:~/models"],
)
def test_validate_storage_path_reports_invalid_path(storage_path: str) -> None:
    client = _make_storage_client()

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert len(errors) == 1
    assert errors[0].message.startswith(f"Storage path '{storage_path}' is invalid")
    client.storage.stat.assert_not_awaited()


@pytest.mark.parametrize(
    "validator_config",
    [
        {"same_project": True},
        {"exists": False, "same_project": True},
        {"exists": False, "is_dir": False},
    ],
)
def test_validate_storage_path_skips_stat_without_existence_checks(
    validator_config: dict[str, bool],
) -> None:
    client = _make_storage_client(stat_error=ResourceNotFound("404: Not Found"))

    errors = _validate_storage_path(
        {"files_path": {"path": "storage:models"}}, client, validator_config
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


class _StorageTransport:
    def __init__(self, directories: set[str]) -> None:
        self.directories = directories
        self.urls: list[URL] = []

    @asynccontextmanager
    async def request(
        self, method: str, url: URL, *, auth: str
    ) -> AsyncIterator[SimpleNamespace]:
        self.urls.append(url)
        storage_path = url.path.removeprefix("/storage")
        if storage_path not in self.directories:
            msg = "404: Not Found"
            raise ResourceNotFound(msg)
        yield SimpleNamespace(
            headers={},
            json=AsyncMock(
                return_value={
                    "FileStatus": {
                        "path": storage_path,
                        "type": "DIRECTORY",
                        "length": 0,
                        "modificationTime": 0,
                        "permission": "read",
                    }
                }
            ),
        )


def _make_sdk_storage_client(transport: _StorageTransport) -> MagicMock:
    client = _make_storage_client()
    config = MagicMock()
    config.project_name_or_raise = "test-project"
    config.cluster_name = "cluster"
    config.org_name = "test-org"
    config.get_cluster.return_value = SimpleNamespace(
        storage_url=URL("https://storage.test/storage")
    )
    config._api_auth = AsyncMock(return_value="Bearer token")
    storage = SimpleNamespace(_config=config, _core=transport)
    storage._set_time_diff = lambda *args: None
    storage._normalize_uri = MethodType(Storage._normalize_uri, storage)
    storage._get_storage_url = MethodType(Storage._get_storage_url, storage)
    storage.stat = MethodType(Storage.stat, storage)
    client.storage = storage
    return client


@pytest.mark.parametrize(
    ("storage_path", "expected_url", "expected_errors"),
    [
        (
            "storage:models",
            "https://storage.test/storage/test-org/test-project/models?op=GETFILESTATUS",
            [],
        ),
        (
            "storage:missing",
            "https://storage.test/storage/test-org/test-project/missing?op=GETFILESTATUS",
            ["Storage path 'storage:missing' does not exist or is not accessible."],
        ),
        (
            "storage://cluster/test-org/test-project/..%2fother-project/models",
            None,
            ["has a percent-encoded '/' or '.'"],
        ),
        (
            "storage://cluster/test-org/test-project/a%2f..%2f..%2f..%2fother-org%2fother-project/models",
            None,
            ["has a percent-encoded '/' or '.'"],
        ),
    ],
)
def test_validate_storage_path_with_sdk_storage_requests(
    storage_path: str, expected_url: str | None, expected_errors: list[str]
) -> None:
    transport = _StorageTransport(
        {
            "/test-org/test-project/models",
            "/test-org/other-project/models",
            "/other-org/other-project/models",
        }
    )
    client = _make_sdk_storage_client(transport)

    errors = _validate_storage_path({"files_path": {"path": storage_path}}, client)

    assert len(errors) == len(expected_errors)
    for error, expected in zip(errors, expected_errors, strict=True):
        assert expected in error.message
    assert transport.urls == ([URL(expected_url)] if expected_url else [])
