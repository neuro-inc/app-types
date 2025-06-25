import logging
import typing as t

from apolo_app_types import LightRAGAppInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import get_preset, preset_to_resources
from apolo_app_types.helm.apps.ingress import get_http_ingress_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret


logger = logging.getLogger(__name__)


class LightRAGChartValueProcessor(BaseChartValueProcessor[LightRAGAppInputs]):
    async def _get_environment_values(
        self, input_: LightRAGAppInputs, app_secrets_name: str
    ) -> dict[str, t.Any]:
        """Configure environment variables for LightRAG."""

        # Build environment configuration matching the full chart structure
        env_config = {
            "HOST": "0.0.0.0",
            "PORT": 9621,
            # Web UI configuration - using default LightRAG values
            "WEBUI_TITLE": "LightRAG - Graph RAG Engine",
            "WEBUI_DESCRIPTION": "Simple and Fast Graph Based RAG System",
            # LLM configuration
            "LLM_BINDING": input_.llm_config.binding,
            "LLM_MODEL": input_.llm_config.model,
            "LLM_BINDING_HOST": input_.llm_config.host or "",
            "LLM_BINDING_API_KEY": serialize_optional_secret(
                input_.llm_config.api_key, app_secrets_name
            ),
            # Embedding configuration
            "EMBEDDING_BINDING": input_.embedding_config.binding,
            "EMBEDDING_MODEL": input_.embedding_config.model,
            "EMBEDDING_DIM": input_.embedding_config.dimensions,
            "EMBEDDING_BINDING_API_KEY": serialize_optional_secret(
                input_.embedding_config.api_key, app_secrets_name
            ),
            # Storage configuration - hardcoded to match minimal setup
            "LIGHTRAG_KV_STORAGE": "PGKVStorage",
            "LIGHTRAG_VECTOR_STORAGE": "PGVectorStorage",
            "LIGHTRAG_DOC_STATUS_STORAGE": "PGDocStatusStorage",
            "LIGHTRAG_GRAPH_STORAGE": "NetworkXStorage",
            # PostgreSQL connection using Crunchy Postgres app outputs
            "POSTGRES_HOST": input_.pgvector_user.pgbouncer_host,
            "POSTGRES_PORT": input_.pgvector_user.pgbouncer_port,
            "POSTGRES_USER": input_.pgvector_user.user,
            "POSTGRES_PASSWORD": input_.pgvector_user.password,
            "POSTGRES_DATABASE": input_.pgvector_user.dbname,
            "POSTGRES_WORKSPACE": "default",
        }

        # NetworkXStorage uses local file storage, no additional configuration needed

        return {"env": env_config}

    async def _get_persistence_values(
        self, input_: LightRAGAppInputs
    ) -> dict[str, t.Any]:
        """Configure persistence values for LightRAG storage volumes."""
        return {
            "persistence": {
                "enabled": True,
                "ragStorage": {
                    "size": f"{input_.persistence.rag_storage_size}Gi",
                },
                "inputs": {
                    "size": f"{input_.persistence.inputs_storage_size}Gi",
                },
            }
        }

    async def gen_extra_values(
        self,
        input_: LightRAGAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for LightRAG Helm chart deployment."""

        # Get component-specific values
        env_values = await self._get_environment_values(input_, app_secrets_name)
        persistence_values = await self._get_persistence_values(input_)
        preset = get_preset(self.client, input_.preset.name)
        resource_values = {"resources": preset_to_resources(preset)}

        ingress_values: dict[str, t.Any] = {"ingress": {"enabled": False}}
        if input_.ingress_http:
            ingress_values["ingress"] = await get_http_ingress_values(
                self.client,
                input_.ingress_http,
                namespace,
                app_id,
                app_type=AppType.LightRAG,
            )

        # Basic chart configuration
        base_values = {
            "replicaCount": 1,
            "image": {
                "repository": "ghcr.io/hkuds/lightrag",
                "tag": "latest",
                "pullPolicy": "IfNotPresent",
            },
            "service": {
                "type": "ClusterIP",
                "port": 9621,
            },
            "nameOverride": "",
            "fullnameOverride": app_name,
        }

        logger.debug("Generated LightRAG values for app %s", app_name)

        # Merge all values together
        return merge_list_of_dicts(
            [
                base_values,
                env_values,
                persistence_values,
                ingress_values,
                resource_values,
            ]
        )
