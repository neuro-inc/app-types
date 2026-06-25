from apolo_app_types.protocols.common.custom_validators import preset_validator
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


def test_schema_extra_metadata_serializes_custom_validators() -> None:
    metadata = SchemaExtraMetadata(
        title="Preset",
        description="Preset requirements",
        custom_validators=[
            {
                "preset_validator": {
                    "exists": True,
                    "min_vram_gb": 10,
                }
            }
        ],
    )

    assert metadata.as_json_schema_extra()["x-custom-validators"] == [
        {
            "preset_validator": {
                "exists": True,
                "min_vram_gb": 10,
            }
        }
    ]


def test_preset_validator_builder_serializes_expected_shape() -> None:
    assert preset_validator(exists=True, min_vram_gb=10) == {
        "preset_validator": {
            "exists": True,
            "min_vram_gb": 10,
        }
    }
