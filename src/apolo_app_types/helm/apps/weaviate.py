import logging
import typing as t

from apolo_app_types import BasicAuth, Bucket, WeaviateInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.buckets import BucketProvider, S3BucketCredentials
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret


WEAVIATE_BUCKET_NAME = "weaviate-backup"


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

    async def _get_backup_values(
        self, backup_bucket: Bucket, app_secrets_name: str
    ) -> dict[str, t.Any]:
        """Configure backup values for Weaviate using Apolo Blob Storage."""

        if backup_bucket.bucket_provider is not BucketProvider.AWS:
            msg = "Only AWS is supported for Weaviate backups."
            raise Exception(msg)

        bucket_credentials = backup_bucket.credentials[0]
        if not isinstance(bucket_credentials, S3BucketCredentials):
            msg = "Only S3 bucket credentials are supported for Weaviate backups."
            raise Exception(msg)

        s3_endpoint = bucket_credentials.endpoint_url.replace("https://", "")

        if not all(
            [
                bucket_credentials.name,
                bucket_credentials.access_key_id,
                bucket_credentials.secret_access_key,
                s3_endpoint,
                bucket_credentials.region_name,
            ]
        ):
            msg = "Missing required args for setting up Apolo Blob Storage"
            raise Exception(msg)

        return {
            "s3": {
                "enabled": True,
                "envconfig": {
                    "BACKUP_S3_BUCKET": backup_bucket.id,
                    "BACKUP_S3_ENDPOINT": s3_endpoint,
                    "BACKUP_S3_REGION": bucket_credentials.region_name,
                },
                "secrets": {
                    "AWS_ACCESS_KEY_ID": serialize_optional_secret(
                        bucket_credentials.access_key_id, secret_name=app_secrets_name
                    ),
                    "AWS_SECRET_ACCESS_KEY": serialize_optional_secret(
                        bucket_credentials.secret_access_key,
                        secret_name=app_secrets_name,
                    ),
                },
            }
        }

    async def gen_extra_values(
        self,
        input_: WeaviateInputs,
        app_name: str,
        namespace: str,
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
        )

        # TODO: temporarily removed cluster_api from WeaviateInputs and
        # relying on ingress_http and ingress_grpc auth level.
        # Will make it available again later.
        # if input_.cluster_api:
        #     auth_vals = await self._get_auth_values(input_.cluster_api)
        # else:
        #     auth_vals = {}

        # Configure backups if enabled
        if input_.backup_bucket:
            values["backups"] = await self._get_backup_values(
                input_.backup_bucket, app_secrets_name
            )

        logger.debug("Generated extra Weaviate values: %s", values)
        return merge_list_of_dicts(
            [
                values,
                # auth_vals,
                {"storage": {"size": f"{input_.persistence.size}Gi"}},
            ]
        )
