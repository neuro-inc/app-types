import logging
import secrets
import typing as t

import apolo_sdk

from apolo_app_types import LightRAGInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.buckets import get_or_create_bucket_credentials
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts


logger = logging.getLogger(__name__)


class LightRAGChartValueProcessor(BaseChartValueProcessor[LightRAGInputs]):
    async def _get_secret_values(self, input_: LightRAGInputs) -> dict[str, t.Any]:
        """Configure secret values for LightRAG API keys."""
        values: dict[str, t.Any] = {}

        # API key secrets that will be mounted as environment variables
        secrets_data = {}

        if input_.llm_config.api_key:
            secrets_data["LLM_BINDING_API_KEY"] = input_.llm_config.api_key

        if input_.embedding_config.api_key:
            secrets_data["EMBEDDING_BINDING_API_KEY"] = input_.embedding_config.api_key

        if secrets_data:
            values["secrets"] = {"lightragApiKeys": secrets_data}

        return values

    async def _get_backup_values(self, app_name: str) -> dict[str, t.Any]:
        """Configure backup values for LightRAG using Apolo Blob Storage."""

        name = f"app-lightrag-backup-{app_name}"

        bucket_credentials = await get_or_create_bucket_credentials(
            client=self.client,
            bucket_name=name,
            credentials_name=name,
            supported_providers=[
                apolo_sdk.Bucket.Provider.AWS,
                apolo_sdk.Bucket.Provider.MINIO,
            ],
        )

        s3_endpoint = (
            bucket_credentials.credentials[0]
            .credentials["endpoint_url"]
            .replace("https://", "")
        )
        bucket_name = bucket_credentials.credentials[0].credentials["bucket_name"]
        access_key_id = bucket_credentials.credentials[0].credentials["access_key_id"]
        secret_access_key = bucket_credentials.credentials[0].credentials[
            "secret_access_key"
        ]
        region_name = bucket_credentials.credentials[0].credentials["region_name"]

        return {
            "s3": {
                "enabled": True,
                "envconfig": {
                    "BACKUP_S3_BUCKET": bucket_name,
                    "BACKUP_S3_ENDPOINT": s3_endpoint,
                    "BACKUP_S3_REGION": region_name,
                },
                "secrets": {
                    "AWS_ACCESS_KEY_ID": access_key_id,
                    "AWS_SECRET_ACCESS_KEY": secret_access_key,
                },
            }
        }

    async def _get_postgres_values(self, input_: LightRAGInputs) -> dict[str, t.Any]:
        """Configure PostgreSQL values for LightRAG."""
        values: dict[str, t.Any] = {}

        # PostgreSQL configuration with pgvector extension
        values["postgresql"] = {
            "enabled": True,
            "image": {
                "registry": "docker.io",
                "repository": "pgvector/pgvector",
                "tag": "pg16",
            },
            "auth": {
                "database": "lightrag",
                "username": "lightrag_user",
                "password": secrets.token_urlsafe(16),
            },
            "primary": {
                "persistence": {
                    "enabled": True,
                    "size": f"{input_.persistence.postgres_storage_size}Gi",
                },
                "resources": {
                    "limits": {
                        "cpu": "1000m",
                        "memory": "2Gi",
                    },
                    "requests": {
                        "cpu": "250m",
                        "memory": "512Mi",
                    },
                },
                "initdb": {
                    "scripts": {
                        "00-pgvector.sql": "CREATE EXTENSION IF NOT EXISTS vector;",
                    },
                },
            },
        }

        return values

    async def _get_persistence_values(self, input_: LightRAGInputs) -> dict[str, t.Any]:
        """Configure persistence values for LightRAG storage."""
        values: dict[str, t.Any] = {}

        values["persistence"] = {
            "enabled": True,
            "ragStorage": {
                "accessMode": "ReadWriteOnce",
                "size": f"{input_.persistence.rag_storage_size}Gi",
                "storageClass": "",  # Use default storage class
            },
            "inputs": {
                "accessMode": "ReadWriteOnce",
                "size": f"{input_.persistence.inputs_storage_size}Gi",
                "storageClass": "",  # Use default storage class
            },
        }

        return values

    async def _get_environment_values(self, input_: LightRAGInputs) -> dict[str, t.Any]:
        """Configure environment variables for LightRAG."""
        values: dict[str, t.Any] = {}

        # Base environment configuration
        env_config = {
            "HOST": "0.0.0.0",
            "PORT": "9621",
            # Web UI configuration
            "WEBUI_TITLE": input_.webui_config.title,
            "WEBUI_DESCRIPTION": input_.webui_config.description,
            # LLM configuration
            "LLM_BINDING": input_.llm_config.binding,
            "LLM_MODEL": input_.llm_config.model,
            "LLM_BINDING_HOST": input_.llm_config.host,
            # Embedding configuration
            "EMBEDDING_BINDING": input_.embedding_config.binding,
            "EMBEDDING_MODEL": input_.embedding_config.model,
            "EMBEDDING_DIM": str(input_.embedding_config.dimensions),
            # Storage configuration - using PostgreSQL for all storage types
            "LIGHTRAG_KV_STORAGE": "PGKVStorage",
            "LIGHTRAG_VECTOR_STORAGE": "PGVectorStorage",
            "LIGHTRAG_DOC_STATUS_STORAGE": "PGDocStatusStorage",
            # Local storage, no external DB needed
            "LIGHTRAG_GRAPH_STORAGE": "NetworkXStorage",
            # PostgreSQL connection (internal service)
            "POSTGRES_HOST": '{{ include "lightrag-minimal.fullname" . }}-postgresql',
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "lightrag_user",
            "POSTGRES_DATABASE": "lightrag",
            "POSTGRES_WORKSPACE": "default",
        }

        values["env"] = env_config

        return values

    async def gen_extra_values(
        self,
        input_: LightRAGInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for LightRAG configuration."""

        # Get base values for ingress and networking
        base_values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress_http=input_.ingress_http,
            namespace=namespace,
        )

        # Get component-specific values
        secret_values = await self._get_secret_values(input_)
        postgres_values = await self._get_postgres_values(input_)
        persistence_values = await self._get_persistence_values(input_)
        env_values = await self._get_environment_values(input_)

        # Configure backups if enabled
        backup_values = {}
        if input_.persistence.enable_backups:
            backup_values = await self._get_backup_values(app_name)

        logger.debug("Generated extra LightRAG values: %s", base_values)

        # Merge all values together
        all_values = [
            base_values,
            secret_values,
            postgres_values,
            persistence_values,
            env_values,
        ]

        if backup_values:
            all_values.append(backup_values)

        return merge_list_of_dicts(all_values)
