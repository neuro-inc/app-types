import pytest

from apolo_app_types.outputs.stable_diffusion import get_stable_diffusion_outputs


@pytest.mark.asyncio
async def test_sd(setup_clients, mock_kubernetes_client):
    res = await get_stable_diffusion_outputs(
        helm_values={
            "model": {"modelHFName": "SD-Model"},
            "env": {"VLLM_API_KEY": "dummy-api-key"},
        }
    )

    assert res
    assert res["external_api"]["host"] == "example.com"
    assert res["external_api"]["base_path"] == "/sdapi/v1"
    assert res["internal_api"]["host"] == "app.default-namespace"
    assert res["internal_api"]["base_path"] == "/sdapi/v1"
    assert res["hf_model"] == {
        "modelHFName": "SD-Model",
        "modelFiles": None,
        "hfToken": None,
    }


@pytest.mark.asyncio
async def test_sd_without_files(setup_clients, mock_kubernetes_client):
    res = await get_stable_diffusion_outputs(
        helm_values={
            "model": {
                "modelHFName": "SD-Model",
            }
        }
    )

    assert res
    assert res["external_api"]["host"] == "example.com"
    assert res["external_api"]["base_path"] == "/sdapi/v1"
    assert res["internal_api"]["host"] == "app.default-namespace"
    assert res["internal_api"]["base_path"] == "/sdapi/v1"
    assert res["hf_model"] == {
        "modelHFName": "SD-Model",
        "hfToken": None,
        "modelFiles": None,
    }


@pytest.mark.asyncio
async def test_sd_without_model(setup_clients, mock_kubernetes_client):
    with pytest.raises(KeyError) as exc_info:
        await get_stable_diffusion_outputs(helm_values={})

    assert str(exc_info.value) == "'model'"
