import pytest

from apolo_app_types.outputs.lightrag import get_lightrag_outputs


@pytest.mark.asyncio
async def test_lightrag_outputs_generation(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with full configuration"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
                "pullPolicy": "IfNotPresent",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "openai",
                "LLM_MODEL": "gpt-4",
                "LLM_BINDING_HOST": "https://api.openai.com:443/v1",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "text-embedding-ada-002",
                "EMBEDDING_DIM": 1536,
                "EMBEDDING_BINDING_HOST": "https://api.openai.com:443/v1",
                "POSTGRES_HOST": "postgres.example.com",
                "POSTGRES_PORT": 5432,
                "POSTGRES_USER": "lightrag_user",
                "POSTGRES_DATABASE": "lightrag_db",
                "WEBUI_TITLE": "Graph RAG Engine",
                "WEBUI_DESCRIPTION": "Simple and Fast Graph Based RAG System",
                "HOST": "0.0.0.0",
                "PORT": 9621,
            },
            "persistence": {
                "enabled": True,
                "ragStorage": {"size": "10Gi"},
                "inputs": {"size": "5Gi"},
            },
            "ingress": {
                "enabled": True,
                "className": "traefik",
                "hosts": [
                    {
                        "host": "lightrag--test-app-id.apps.example.com",
                        "paths": [
                            {"path": "/", "pathType": "Prefix", "portName": "http"}
                        ],
                    }
                ],
                "annotations": {
                    "traefik.ingress.kubernetes.io/router.middlewares": (
                        "platform-platform-control-plane-ingress-auth@kubernetescrd"
                    )
                },
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test web app URLs
    assert res["web_app_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["web_app_url"]["internal_url"]["port"] == 9621
    assert res["web_app_url"]["internal_url"]["protocol"] == "http"

    assert res["web_app_url"]["external_url"]["host"] == "example.com"
    assert res["web_app_url"]["external_url"]["port"] == 80
    assert res["web_app_url"]["external_url"]["protocol"] == "https"

    # Test server URLs (same as web app for LightRAG)
    assert res["server_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["server_url"]["internal_url"]["port"] == 9621
    assert res["server_url"]["internal_url"]["protocol"] == "http"

    assert res["server_url"]["external_url"]["host"] == "example.com"
    assert res["server_url"]["external_url"]["port"] == 80
    assert res["server_url"]["external_url"]["protocol"] == "https"


@pytest.mark.asyncio
async def test_lightrag_outputs_minimal_configuration(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with minimal configuration"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "openai",
                "LLM_MODEL": "gpt-4",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "text-embedding-ada-002",
                "EMBEDDING_DIM": 1536,
                "HOST": "0.0.0.0",
                "PORT": 9621,
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test that internal URLs are generated correctly
    assert res["web_app_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["web_app_url"]["internal_url"]["port"] == 9621
    assert res["web_app_url"]["internal_url"]["protocol"] == "http"

    assert res["server_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["server_url"]["internal_url"]["port"] == 9621
    assert res["server_url"]["internal_url"]["protocol"] == "http"

    # Test that external URLs are generated correctly
    assert res["web_app_url"]["external_url"]["host"] == "example.com"
    assert res["web_app_url"]["external_url"]["port"] == 80
    assert res["web_app_url"]["external_url"]["protocol"] == "https"

    assert res["server_url"]["external_url"]["host"] == "example.com"
    assert res["server_url"]["external_url"]["port"] == 80
    assert res["server_url"]["external_url"]["protocol"] == "https"


@pytest.mark.asyncio
async def test_lightrag_outputs_with_different_service_port(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with different service port"""
    # Save original mock
    original_mock = mock_kubernetes_client[
        "mock_v1_instance"
    ].list_namespaced_service.side_effect

    # Override the mock to return port 8080 for this specific test
    def get_services_by_label_override(namespace, label_selector):
        if (
            label_selector
            == "app.kubernetes.io/name=lightrag,app.kubernetes.io/instance=test-app-instance-id"  # noqa: E501
        ):
            return {
                "items": [
                    {
                        "metadata": {
                            "name": "lightrag",
                            "namespace": namespace,
                        },
                        "spec": {"ports": [{"port": 8080}]},
                    }
                ]
            }
        # Fall back to original mock behavior for other selectors
        return original_mock(namespace, label_selector)

    # Apply the override
    mock_kubernetes_client[
        "mock_v1_instance"
    ].list_namespaced_service.side_effect = get_services_by_label_override

    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 8080,  # Different port
            },
            "env": {
                "LLM_BINDING": "ollama",
                "LLM_MODEL": "llama3.1:8b",
                "EMBEDDING_BINDING": "ollama",
                "EMBEDDING_MODEL": "nomic-embed-text",
                "EMBEDDING_DIM": 1024,
                "HOST": "0.0.0.0",
                "PORT": 8080,
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test internal URLs use the correct port
    assert res["web_app_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["web_app_url"]["internal_url"]["port"] == 8080
    assert res["web_app_url"]["internal_url"]["protocol"] == "http"

    assert res["server_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["server_url"]["internal_url"]["port"] == 8080
    assert res["server_url"]["internal_url"]["protocol"] == "http"

    # Restore original mock
    mock_kubernetes_client[
        "mock_v1_instance"
    ].list_namespaced_service.side_effect = original_mock


@pytest.mark.asyncio
async def test_lightrag_outputs_with_custom_ingress_host(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with custom ingress host"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "anthropic",
                "LLM_MODEL": "claude-3-sonnet-20240229",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "text-embedding-3-small",
                "EMBEDDING_DIM": 1536,
                "HOST": "0.0.0.0",
                "PORT": 9621,
            },
            "ingress": {
                "enabled": True,
                "className": "traefik",
                "hosts": [
                    {
                        "host": "my-custom-lightrag.company.com",
                        "paths": [
                            {"path": "/", "pathType": "Prefix", "portName": "http"}
                        ],
                    }
                ],
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test that custom external host is used
    assert (
        res["web_app_url"]["external_url"]["host"] == "example.com"
    )  # Still uses mock value
    assert res["web_app_url"]["external_url"]["protocol"] == "https"

    assert (
        res["server_url"]["external_url"]["host"] == "example.com"
    )  # Still uses mock value
    assert res["server_url"]["external_url"]["protocol"] == "https"


@pytest.mark.asyncio
async def test_lightrag_outputs_with_gemini_provider(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with Gemini provider"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "gemini",
                "LLM_MODEL": "gemini-1.5-flash",
                "LLM_BINDING_HOST": "https://generativelanguage.googleapis.com:443/v1",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "text-embedding-3-small",
                "EMBEDDING_DIM": 1536,
                "EMBEDDING_BINDING_HOST": "https://api.openai.com:443/v1",
                "HOST": "0.0.0.0",
                "PORT": 9621,
                "WEBUI_TITLE": "Graph RAG Engine",
                "WEBUI_DESCRIPTION": "Simple and Fast Graph Based RAG System",
            },
            "persistence": {
                "enabled": True,
                "ragStorage": {"size": "15Gi"},
                "inputs": {"size": "8Gi"},
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test standard output generation works with Gemini
    assert res["web_app_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["web_app_url"]["internal_url"]["port"] == 9621
    assert res["web_app_url"]["internal_url"]["protocol"] == "http"

    assert res["server_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["server_url"]["internal_url"]["port"] == 9621
    assert res["server_url"]["internal_url"]["protocol"] == "http"


@pytest.mark.asyncio
async def test_lightrag_outputs_with_openai_compatible_providers(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with OpenAI compatible providers"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "openai",
                "LLM_MODEL": "meta-llama/Llama-3.1-8B-Instruct",
                "LLM_BINDING_HOST": "https://my-llm-server.com:8080/v1",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
                "EMBEDDING_DIM": 384,
                "EMBEDDING_BINDING_HOST": "https://my-embedding-server.com:8080/v1",
                "HOST": "0.0.0.0",
                "PORT": 9621,
                "WEBUI_TITLE": "Graph RAG Engine",
                "WEBUI_DESCRIPTION": "Simple and Fast Graph Based RAG System",
                "POSTGRES_HOST": "postgres.example.com",
                "POSTGRES_PORT": 5432,
                "POSTGRES_USER": "lightrag_user",
                "POSTGRES_DATABASE": "lightrag_db",
                "LIGHTRAG_KV_STORAGE": "PGKVStorage",
                "LIGHTRAG_VECTOR_STORAGE": "PGVectorStorage",
                "LIGHTRAG_DOC_STATUS_STORAGE": "PGDocStatusStorage",
                "LIGHTRAG_GRAPH_STORAGE": "NetworkXStorage",
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test output generation works with OpenAI compatible providers
    assert res["web_app_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["web_app_url"]["internal_url"]["port"] == 9621
    assert res["web_app_url"]["internal_url"]["protocol"] == "http"

    assert res["server_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["server_url"]["internal_url"]["port"] == 9621
    assert res["server_url"]["internal_url"]["protocol"] == "http"

    # Test external URLs
    assert res["web_app_url"]["external_url"]["host"] == "example.com"
    assert res["web_app_url"]["external_url"]["port"] == 80
    assert res["web_app_url"]["external_url"]["protocol"] == "https"

    assert res["server_url"]["external_url"]["host"] == "example.com"
    assert res["server_url"]["external_url"]["port"] == 80
    assert res["server_url"]["external_url"]["protocol"] == "https"


@pytest.mark.asyncio
async def test_lightrag_outputs_with_persistence_disabled(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs generation with persistence disabled"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "openai",
                "LLM_MODEL": "gpt-4",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "text-embedding-ada-002",
                "EMBEDDING_DIM": 1536,
                "HOST": "0.0.0.0",
                "PORT": 9621,
            },
            "persistence": {
                "enabled": False,
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test outputs are still generated correctly even without persistence
    assert res["web_app_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["web_app_url"]["internal_url"]["port"] == 9621
    assert res["web_app_url"]["internal_url"]["protocol"] == "http"

    assert res["server_url"]["internal_url"]["host"] == "lightrag.default-namespace"
    assert res["server_url"]["internal_url"]["port"] == 9621
    assert res["server_url"]["internal_url"]["protocol"] == "http"


@pytest.mark.asyncio
async def test_lightrag_outputs_structure_validation(
    setup_clients, mock_kubernetes_client, app_instance_id
):
    """Test LightRAG outputs structure validation"""
    res = await get_lightrag_outputs(
        helm_values={
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "1.3.8",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "env": {
                "LLM_BINDING": "openai",
                "LLM_MODEL": "gpt-4",
                "EMBEDDING_BINDING": "openai",
                "EMBEDDING_MODEL": "text-embedding-ada-002",
                "EMBEDDING_DIM": 1536,
                "HOST": "0.0.0.0",
                "PORT": 9621,
            },
        },
        app_instance_id=app_instance_id,
    )

    # Test that the output structure matches LightRAGAppOutputs
    assert "web_app_url" in res
    assert "server_url" in res

    # Test that both URLs have internal and external components
    assert "internal_url" in res["web_app_url"]
    assert "external_url" in res["web_app_url"]
    assert "internal_url" in res["server_url"]
    assert "external_url" in res["server_url"]

    # Test that URL components have required fields
    for url_key in ["web_app_url", "server_url"]:
        for url_type in ["internal_url", "external_url"]:
            url = res[url_key][url_type]
            assert "host" in url
            assert "port" in url
            assert "protocol" in url
            assert isinstance(url["port"], int)
            assert url["protocol"] in ["http", "https"]
