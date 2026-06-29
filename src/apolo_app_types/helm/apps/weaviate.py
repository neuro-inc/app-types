import logging
import secrets
import typing as t

import apolo_sdk

from apolo_app_types import BasicAuth, WeaviateInputs
from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.buckets import get_or_create_bucket_credentials
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts


logger = logging.getLogger(__name__)


class WeaviateChartValueProcessor(BaseChartValueProcessor[WeaviateInputs]):
    async def _get_auth_values(self, cluster_api: BasicAuth) -> dict[str, t.Any]:
        """Configure authentication values for Weaviate."""
        values: dict[str, t.Any] = {}

        values["clusterApi"] = {
            "username": cluster_api.username,
            "password": cluster_api.password,
        }

        values["authentication"] = {
            "anonymous_access": {"enabled": False},
            "apikey": {
                "enabled": True,
                "allowed_keys": [cluster_api.password],
                "users": [cluster_api.username],
            },
        }
        values["env"] = {
            "AUTHENTICATION_APIKEY_ENABLED": True,
            "AUTHENTICATION_APIKEY_ALLOWED_KEYS": cluster_api.password,
            "AUTHENTICATION_APIKEY_USERS": cluster_api.username,
        }
        values["authorization"] = {
            "admin_list": {
                "enabled": True,
                "users": [cluster_api.username],
            }
        }

        return values

    async def _get_backup_values(self, app_name: str) -> dict[str, t.Any]:
        """Configure backup values for Weaviate using Apolo Blob Storage."""

        name = f"app-weaviate-backup-{app_name}"

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

    async def _generate_user_credentials(self) -> dict[str, t.Any]:
        """Generate user credentials for Weaviate, using a random password."""
        values: dict[str, t.Any] = {}
        values["clusterApi"] = {
            "username": "admin",
            "password": secrets.token_urlsafe(16),
        }
        return values

    async def gen_extra_values(
        self,
        input_: WeaviateInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for Weaviate configuration."""

        # Get base values
        values = await gen_extra_values(
            apolo_client=self.client,
            preset_type=input_.preset,
            ingress_http=input_.ingress_http,
            # ingress_grpc=input_.ingress_grpc,
            namespace=namespace,
            app_id=app_id,
            app_type=AppType.Weaviate,
        )

        # TODO: temporarily removed cluster_api from WeaviateInputs and
        # relying on ingress_http and ingress_grpc auth level.
        # Will make it available again later.
        # if input_.cluster_api:
        #     auth_vals = await self._get_auth_values(input_.cluster_api)
        # else:
        #     auth_vals = {}

        auth_vals = await self._generate_user_credentials()
        # Configure backups if enabled
        if input_.persistence.enable_backups:
            values["backups"] = await self._get_backup_values(app_name)

        logger.debug("Generated extra Weaviate values: %s", values)
        return merge_list_of_dicts(
            [
                values,
                auth_vals,
                {"storage": {"size": f"{input_.persistence.size}Gi"}},
            ]
        )
