import logging
import typing as t

from apolo_app_types import LightRAGAppInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.ingress import get_http_ingress_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts


logger = logging.getLogger(__name__)


class LightRAGChartValueProcessor(BaseChartValueProcessor[LightRAGAppInputs]):
    async def _get_environment_values(
        self, input_: LightRAGAppInputs
    ) -> dict[str, t.Any]:
        """Configure environment variables for LightRAG."""

        # Build environment configuration matching the full chart structure
        env_config = {
            "HOST": "0.0.0.0",
            "PORT": 9621,
            # Web UI configuration
            "WEBUI_TITLE": input_.webui_config.title,
            "WEBUI_DESCRIPTION": input_.webui_config.description,
            # LLM configuration
            "LLM_BINDING": input_.llm_config.binding,
            "LLM_MODEL": input_.llm_config.model,
            "LLM_BINDING_HOST": input_.llm_config.host or "",
            "LLM_BINDING_API_KEY": input_.llm_config.api_key or "",
            # Embedding configuration
            "EMBEDDING_BINDING": input_.embedding_config.binding,
            "EMBEDDING_MODEL": input_.embedding_config.model,
            "EMBEDDING_DIM": input_.embedding_config.dimensions,
            "EMBEDDING_BINDING_API_KEY": input_.embedding_config.api_key or "",
            # Storage configuration using PostgreSQL backends
            "LIGHTRAG_KV_STORAGE": input_.storage_config.kv_storage,
            "LIGHTRAG_VECTOR_STORAGE": input_.storage_config.vector_storage,
            "LIGHTRAG_GRAPH_STORAGE": input_.storage_config.graph_storage,
            "LIGHTRAG_DOC_STATUS_STORAGE": input_.storage_config.doc_status_storage,
            # PostgreSQL connection using Crunchy Postgres app outputs
            "POSTGRES_HOST": input_.pgvector_user.pgbouncer_host,
            "POSTGRES_PORT": input_.pgvector_user.pgbouncer_port,
            "POSTGRES_USER": input_.pgvector_user.user,
            "POSTGRES_PASSWORD": input_.pgvector_user.password,
            "POSTGRES_DATABASE": input_.pgvector_user.dbname or "postgres",
            "POSTGRES_WORKSPACE": "default",
        }

        # Add optional Neo4J configuration if using Neo4J graph storage
        if input_.storage_config.graph_storage == "Neo4JStorage":
            env_config.update(
                {
                    "NEO4J_URI": "neo4j://neo4j-cluster-neo4j:7687",
                    "NEO4J_USERNAME": "neo4j",
                    "NEO4J_PASSWORD": "",  # Will be configured via secret if needed
                }
            )

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

    async def _get_resource_values(self, input_: LightRAGAppInputs) -> dict[str, t.Any]:
        """Configure resource limits and requests based on preset."""
        # Basic resource configuration - can be enhanced based on preset details
        return {
            "resources": {
                "limits": {
                    "cpu": "2000m",
                    "memory": "4Gi",
                },
                "requests": {
                    "cpu": "500m",
                    "memory": "1Gi",
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
        env_values = await self._get_environment_values(input_)
        persistence_values = await self._get_persistence_values(input_)
        resource_values = await self._get_resource_values(input_)

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
