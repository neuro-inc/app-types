import pytest

from apolo_app_types.outputs.launchpad import get_launchpad_outputs


KEYCLOAK_HELM_VALUES = {
    "keycloak": {
        "auth": {
            "adminPassword": "test-admin-password",
        }
    },
}


@pytest.mark.asyncio
async def test_launchpad_output_generation(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test launchpad output generation for app_url."""
    res = await get_launchpad_outputs(
        helm_values={
            "LAUNCHPAD_INITIAL_CONFIG": {
                "vllm": {
                    "hugging_face_model": {
                        "model_hf_name": "meta-llama/Llama-3.1-8B-Instruct"
                    },
                    "preset": {"name": "gpu-small"},
                }
            },
            **KEYCLOAK_HELM_VALUES,
        },
        app_instance_id=app_instance_id,
    )

    assert res
    assert "app_url" in res

    app_url = res["app_url"]
    assert app_url["internal_url"] == {
        "base_path": "/",
        "host": "app.default-namespace",
        "port": 80,
        "protocol": "http",
        "timeout": 30.0,
    }
    assert app_url["external_url"] == {
        "base_path": "/",
        "host": "example.com",
        "port": 80,
        "protocol": "https",
        "timeout": 30.0,
    }


@pytest.mark.asyncio
async def test_launchpad_output_generation_no_external_url(
    setup_clients, mock_kubernetes_client, app_instance_id, monkeypatch
):
    """Test launchpad output generation when no external URL is available."""

    async def mock_get_service_host_port(*args, **kwargs):
        return ("app.default-namespace", 80)

    async def mock_get_ingress_host_port(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "apolo_app_types.outputs.launchpad.get_service_host_port",
        mock_get_service_host_port,
    )
    monkeypatch.setattr(
        "apolo_app_types.outputs.launchpad.get_ingress_host_port",
        mock_get_ingress_host_port,
    )

    res = await get_launchpad_outputs(
        helm_values={
            "LAUNCHPAD_INITIAL_CONFIG": {
                "vllm": {
                    "hugging_face_model": {
                        "model_hf_name": "unsloth/Magistral-Small-2506-GGUF"
                    },
                    "preset": {"name": "gpu-medium"},
                }
            },
            **KEYCLOAK_HELM_VALUES,
        },
        app_instance_id=app_instance_id,
    )

    assert res
    assert "app_url" in res

    app_url = res["app_url"]
    assert app_url["internal_url"] == {
        "base_path": "/",
        "host": "app.default-namespace",
        "port": 80,
        "protocol": "http",
        "timeout": 30.0,
    }
    assert app_url["external_url"] is None


@pytest.mark.asyncio
async def test_launchpad_output_generation_no_service(
    setup_clients, mock_kubernetes_client, app_instance_id, monkeypatch
):
    """Test launchpad output generation when no service is available."""

    async def mock_get_service_host_port(*args, **kwargs):
        return (None, None)

    async def mock_get_ingress_host_port(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "apolo_app_types.outputs.launchpad.get_service_host_port",
        mock_get_service_host_port,
    )
    monkeypatch.setattr(
        "apolo_app_types.outputs.launchpad.get_ingress_host_port",
        mock_get_ingress_host_port,
    )

    res = await get_launchpad_outputs(
        helm_values={
            "LAUNCHPAD_INITIAL_CONFIG": {
                "vllm": {
                    "hugging_face_model": {
                        "model_hf_name": "meta-llama/Llama-3.1-8B-Instruct"
                    },
                    "preset": {"name": "gpu-small"},
                }
            },
            **KEYCLOAK_HELM_VALUES,
        },
        app_instance_id=app_instance_id,
    )

    assert res
    assert "app_url" in res

    app_url = res["app_url"]
    assert app_url["internal_url"] is None
    assert app_url["external_url"] is None
    assert res["keycloak_config"]["auth_admin_password"] == "test-admin-password"


@pytest.mark.asyncio
async def test_launchpad_output_generation_custom_ports(
    setup_clients, mock_kubernetes_client, app_instance_id, monkeypatch
):
    """Test launchpad output generation with custom ports."""

    async def mock_get_service_host_port(*args, **kwargs):
        return ("launchpad-service.namespace", 8080)

    async def mock_get_ingress_host_port(*args, **kwargs):
        return ("launchpad.custom.domain", 443)

    monkeypatch.setattr(
        "apolo_app_types.outputs.launchpad.get_service_host_port",
        mock_get_service_host_port,
    )
    monkeypatch.setattr(
        "apolo_app_types.outputs.launchpad.get_ingress_host_port",
        mock_get_ingress_host_port,
    )

    res = await get_launchpad_outputs(
        helm_values={
            "LAUNCHPAD_INITIAL_CONFIG": {
                "vllm": {
                    "hugging_face_model": {
                        "model_hf_name": "meta-llama/Llama-3.1-8B-Instruct"
                    },
                    "preset": {"name": "gpu-large"},
                }
            },
            **KEYCLOAK_HELM_VALUES,
        },
        app_instance_id=app_instance_id,
    )

    assert res
    assert "app_url" in res

    app_url = res["app_url"]
    assert app_url["internal_url"] == {
        "base_path": "/",
        "host": "launchpad-service.namespace",
        "port": 8080,
        "protocol": "http",
        "timeout": 30.0,
    }
    assert app_url["external_url"] == {
        "base_path": "/",
        "host": "launchpad.custom.domain",
        "port": 443,
        "protocol": "https",
        "timeout": 30.0,
    }
