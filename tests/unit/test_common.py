from unittest.mock import MagicMock

import pytest

from apolo_app_types.helm.apps.common import get_preset


def test_get_preset_raises_value_error_when_preset_not_found():
    client = MagicMock()
    client.config.cluster_name = "test-cluster"
    client.config.presets = {"gpu-small": MagicMock()}

    with pytest.raises(ValueError) as exc_info:
        get_preset(client, "invalid")

    assert str(exc_info.value) == "Preset invalid not exist in cluster test-cluster"
