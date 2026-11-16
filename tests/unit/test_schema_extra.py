import pytest

from apolo_app_types.protocols.common.custom_validators import (
    preset_validator,
    storage_path_validator,
)
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


def test_schema_extra_metadata_serializes_custom_validators() -> None:
    metadata = SchemaExtraMetadata(
        title="Preset",
        description="Preset requirements",
        custom_validators=[
            preset_validator(exists=True, min_vram_gib=10),
        ],
    )

    assert metadata.as_json_schema_extra()["x-custom-validators"] == [
        {
            "preset_validator": {
                "exists": True,
                "min_vram_gib": 10,
            }
        }
    ]


def test_preset_validator_builder_serializes_expected_shape() -> None:
    assert preset_validator(
        exists=True,
        min_cpu_cores=2.5,
        min_ram_gib=16,
        min_vram_gib=10,
    ) == {
        "preset_validator": {
            "exists": True,
            "min_cpu_cores": 2.5,
            "min_ram_gib": 16,
            "min_vram_gib": 10,
        }
    }


def test_preset_validator_builder_defaults_to_empty_config() -> None:
    assert preset_validator() == {"preset_validator": {}}


def test_storage_path_validator_builder_serializes_expected_shape() -> None:
    assert storage_path_validator(exists=True, is_dir=True, same_project=True) == {
        "storage_path_validator": {
            "exists": True,
            "is_dir": True,
            "same_project": True,
        }
    }


def test_storage_path_validator_builder_defaults_to_empty_config() -> None:
    assert storage_path_validator() == {"storage_path_validator": {}}


def test_storage_path_validator_builder_rejects_is_dir_without_exists() -> None:
    with pytest.raises(ValueError, match="cannot require a directory"):
        storage_path_validator(exists=False, is_dir=True)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"exists": True, "is_dir": True}, {"exists": True, "is_dir": True}),
        ({"exists": True, "is_dir": False}, {"exists": True, "is_dir": False}),
        ({"exists": False, "is_dir": False}, {"exists": False, "is_dir": False}),
        ({"exists": False}, {"exists": False}),
        ({"is_dir": True}, {"is_dir": True}),
        ({"is_dir": False}, {"is_dir": False}),
    ],
)
def test_storage_path_validator_builder_allows_consistent_flags(
    kwargs: dict[str, bool], expected: dict[str, bool]
) -> None:
    assert storage_path_validator(**kwargs) == {"storage_path_validator": expected}
