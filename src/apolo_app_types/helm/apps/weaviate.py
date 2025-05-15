import logging
import secrets
import typing as t

import apolo_sdk

from apolo_app_types import BasicAuth, WeaviateInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret


logger = logging.getLogger(__name__)


class WeaviateChartValueProcessor(BaseChartValueProcessor[WeaviateInputs]):
    async def _get_auth_values(self, cluster_api: BasicAuth) -> dict[str, t.Any]:
        """Configure authentication values for Weaviate."""
        values: dict[str, t.Any] = {}

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

    async def _generate_user_credentials(self) -> dict[str, t.Any]:
        """Generate user credentials for Weaviate, using a random password."""
        values: dict[str, t.Any] = {}
        values["clusterApi"] = {
            "username": "admin",
            "password": secrets.token_urlsafe(16),
        }
        return values

    async def _get_backup_values(
        self, input_: WeaviateInputs, app_name: str, app_secrets_name: str
    ) -> dict[str, t.Any]:
        """Configure backup values for Weaviate using Apolo Blob Storage.
        Creates the bucket and credentials if they don't exist.
        """
        if not input_.backup_bucket.enable:
            return {}

        bucket_name = f"weaviate-backup-{app_name}"
        credentials_name = (
            bucket_name  # Use the same name for credentials for simplicity
        )

        try:
            # Ensure bucket exists
            try:
                bucket = await self.client.buckets.get(bucket_id_or_name=bucket_name)
                logger.info(
                    "Found existing bucket %s, using it as a backup target",
                    bucket_name,
                )
            except apolo_sdk.ResourceNotFound:
                bucket = await self.client.buckets.create(name=bucket_name)
                logger.info("Created new bucket %s for backups", bucket_name)

            # Ensure persistent credentials exist
            try:
                sdk_bucket_credentials = (
                    await self.client.buckets.persistent_credentials_get(
                        credential_id_or_name=credentials_name,
                    )
                )
                logger.info("Found existing bucket credentials %s", credentials_name)
            except apolo_sdk.ResourceNotFound:
                sdk_bucket_credentials = (
                    await self.client.buckets.persistent_credentials_create(
                        bucket_ids=[bucket.id],
                        name=credentials_name,
                        read_only=False,
                    )
                )
                logger.info("Created new bucket credentials %s", credentials_name)

        except Exception as e:
            logger.error(
                "Failed to ensure bucket/credentials for %s: %s", bucket_name, e
            )
            msg = f"Failed to set up backup bucket {bucket_name}: {e}"
            raise Exception(msg) from e

        # We expect one set of credentials for the newly created/fetched ones.
        if not sdk_bucket_credentials.credentials:
            msg = f"No credentials found or created for bucket {bucket_name}."
            raise Exception(msg)

        # Use the first set of credentials
        # (persistent_credentials_create can associate with multiple buckets,
        # but here we create for one)
        cred_detail = sdk_bucket_credentials.credentials[0]
        provider = cred_detail.provider
        creds_dict = cred_detail.credentials

        if provider not in (
            apolo_sdk.Bucket.Provider.AWS,
            apolo_sdk.Bucket.Provider.MINIO,
        ):
            msg = (
                f"Only AWS and Minio providers are supported for Weaviate backups. "
                f"Found: {provider}"
            )
            raise Exception(msg)

        s3_bucket_name = creds_dict.get("bucket_name")
        s3_endpoint = str(creds_dict.get("endpoint_url", "")).replace("https://", "")
        s3_region = creds_dict.get("region_name")
        s3_access_key_id = creds_dict.get("access_key_id")
        s3_secret_access_key = creds_dict.get("secret_access_key")

        if not all(
            [
                s3_bucket_name,
                s3_access_key_id,
                s3_secret_access_key,
                s3_endpoint,
                s3_region,
            ]
        ):
            msg = (
                f"Missing required S3 credentials details for bucket {bucket_name} "
                f"after fetching/creating. "
                f"Check bucket credentials '{credentials_name}'."
            )
            raise Exception(msg)

        return {
            "backups": {
                "s3": {
                    "enabled": True,
                    "envconfig": {
                        "BACKUP_S3_BUCKET": s3_bucket_name,
                        "BACKUP_S3_ENDPOINT": s3_endpoint,
                        "BACKUP_S3_REGION": s3_region,
                    },
                    "secrets": {
                        "AWS_ACCESS_KEY_ID": serialize_optional_secret(
                            s3_access_key_id, secret_name=app_secrets_name
                        ),
                        "AWS_SECRET_ACCESS_KEY": serialize_optional_secret(
                            s3_secret_access_key,
                            secret_name=app_secrets_name,
                        ),
                    },
                }
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
            namespace=namespace,
        )

        auth_vals = await self._generate_user_credentials()

        # Configure backups if enabled (logic moved into _get_backup_values)
        backup_config_values = await self._get_backup_values(
            input_, app_name, app_secrets_name
        )  # backup_config_values will be {} if not enabled or an error occurs

        logger.debug(
            "Generated extra Weaviate values (pre-merge): base=%s, auth=%s, backup=%s",
            values,
            auth_vals,
            backup_config_values,
        )

        final_values = merge_list_of_dicts(
            [
                values,
                auth_vals,
                {"storage": {"size": f"{input_.persistence.size}Gi"}},
                backup_config_values,  # Merging the backup config values here
            ]
        )
        logger.debug("Final merged Weaviate values: %s", final_values)
        return final_values
