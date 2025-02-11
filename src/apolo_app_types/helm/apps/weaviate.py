import logging
import typing as t

import click
from apolo_app_types import WeaviateInputs, BasicAuth, Bucket

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.ingress import _generate_ingress_config
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common import Ingress
from apolo_app_types.protocols.common.buckets import S3BucketCredentials, BucketProvider

WEAVIATE_BUCKET_NAME = "weaviate-backup"


logger = logging.getLogger(__name__)


class WeaviateChartValueProcessor(BaseChartValueProcessor[WeaviateInputs]):

    async def _get_auth_values(
        self, cluster_api: BasicAuth
    ) -> dict[str, t.Any]:
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

    async def _get_ingress_values(
        self, ingress: Ingress, namespace: str
    ) -> dict[str, t.Any]:
        """Configure ingress values for Weaviate."""
        values: dict[str, t.Any] = {"enabled": False, "grpc": {"enabled": False}}

        if ingress.enabled == "true":
            ingress_config = await _generate_ingress_config(self.client, namespace)
            values.update(
                {
                    "enabled": True,
                    "className": "traefik",
                    "hosts": ingress_config["hosts"],
                }
            )

        if ingress.grpc and ingress.grpc.enabled == "true":
            grpc_ingress_config = await _generate_ingress_config(
                self.client, namespace, namespace_suffix="-grpc"
            )
            values["grpc"] = {
                "enabled": True,
                "className": "traefik",
                "hosts": grpc_ingress_config["hosts"],
                "annotations": {
                    "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
                    "traefik.ingress.kubernetes.io/service.serversscheme": "h2c",
                },
            }

        return values

    async def _get_backup_values(self, backup_bucket: Bucket) -> dict[str, t.Any]:
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
            raise click.ClickException(msg)

        return {
            "s3": {
                "enabled": True,
                "envconfig": {
                    "BACKUP_S3_BUCKET": bucket_credentials.name,
                    "BACKUP_S3_ENDPOINT": s3_endpoint,
                    "BACKUP_S3_REGION": bucket_credentials.region_name,
                },
                "secrets": {
                    "AWS_ACCESS_KEY_ID": bucket_credentials.access_key_id,
                    "AWS_SECRET_ACCESS_KEY": bucket_credentials.secret_access_key,
                },
            }
        }

    async def gen_extra_values(
        self,
        input_: WeaviateInputs,
        app_name: str,
        namespace: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """Generate extra values for Weaviate configuration."""

        # Get base values
        values = await gen_extra_values(self.client, input_.preset, input_.ingress, namespace)

        # Add authentication values
        if input_.clusterApi:
            auth_vals = await self._get_auth_values(input_.clusterApi)
        else:
            auth_vals = {}

        # Configure ingress
        ingress_vals = await self._get_ingress_values(
            input_.ingress, namespace
        )

        # Configure backups if enabled
        if input_.backup_bucket:
            values["backups"] = await self._get_backup_values(input_.backup_bucket)

        logger.debug("Generated extra Weaviate values: %s", values)
        return merge_list_of_dicts(
            [
                values,
                auth_vals,
                {"ingress": ingress_vals},
                {"storage": {"size": f"{input_.persistence.size}Gi"}},
            ]
        )
