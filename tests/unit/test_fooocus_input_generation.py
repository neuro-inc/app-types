import pytest

from apolo_app_types import (
    Container,
    ContainerImage,
    Env,
    Service,
)
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import Ingress, Preset
from apolo_app_types.protocols.common.storage import (
    ApoloFilesMount,
    ApoloFilesPath,
    ApoloMountMode,
    MountPath,
)
from apolo_app_types.protocols.fooocus import (
    FooocusAppInputs, FooocusSpecificAppInputs,
)


@pytest.mark.asyncio
async def test_fooocus_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=FooocusAppInputs(
            preset=Preset(name="cpu-small"),
            ingress=Ingress(
                enabled=True,
                clusterName="default",
            ),
            fooocus_specific=FooocusSpecificAppInputs(
                http_auth=True,
                huggingface_token_secret="RAW_STRING"
            )
        ),
        apolo_client=setup_clients,
        app_type=AppType.Fooocus,
        app_name="fooocus-app",
        namespace="default-namespace",
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/neuro-inc/fooocus",
        "tag": "latest",
    }

    assert helm_params["service"] == {
        "enabled": True,
        "port": 7865,
    }

    assert "podAnnotations" in helm_params
    annotations = helm_params["podAnnotations"]
    assert "platform.apolo.us/inject-storage" in annotations

    from json import loads

    storage_json = annotations["platform.apolo.us/inject-storage"]
    parsed_storage = loads(storage_json)
    assert len(parsed_storage) == 2

    assert parsed_storage[0]["storage_path"] == "storage://mycluster/myorg/myproj/data"
    assert parsed_storage[0]["mount_path"] == "/app/data"
    assert parsed_storage[0]["mount_mode"] == "rw"

    assert parsed_storage[1]["storage_path"] == "storage://mycluster/myorg/config"
    assert parsed_storage[1]["mount_path"] == "/config"
    assert parsed_storage[1]["mount_mode"] == "r"

    pod_labels = helm_params.get("podExtraLabels", {})
    assert pod_labels.get("platform.apolo.us/inject-storage") == "true"
