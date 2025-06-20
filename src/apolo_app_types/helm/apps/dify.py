import secrets
import typing as t

import apolo_sdk

from apolo_app_types.app_types import AppType
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.ingress import get_http_ingress_values
from apolo_app_types.helm.utils.buckets import get_or_create_bucket_credentials
from apolo_app_types.protocols.dify import DifyAppInputs


class DifyChartValueProcessor(BaseChartValueProcessor[DifyAppInputs]):
    async def _get_or_create_dify_blob_storage_values(
        self, input_: DifyAppInputs, app_name: str
    ) -> dict[str, t.Any]:
        # dify chart supports External S3 / Azure / OSS (Alibaba)
        # Otherwise, dify needs ReadWriteMany PVC, which will be supported later

        name = f"app-dify-{app_name}"
        bucket_credentials = await get_or_create_bucket_credentials(
            client=self.client,
            bucket_name=name,
            credentials_name=name,
            supported_providers=[
                apolo_sdk.Bucket.Provider.AWS,
                apolo_sdk.Bucket.Provider.MINIO,
            ],
        )
        return {
            "externalS3": {
                "enabled": True,
                "endpoint": bucket_credentials.credentials[0].credentials[
                    "endpoint_url"
                ],
                "accessKey": bucket_credentials.credentials[0].credentials[
                    "access_key_id"
                ],
                "secretKey": bucket_credentials.credentials[0].credentials[
                    "secret_access_key"
                ],
                "bucketName": bucket_credentials.credentials[0].credentials[
                    "bucket_name"
                ],
            }
        }

        # bucket_name = input_.bucket.id

        # if input_.bucket.bucket_provider not in (
        #     BucketProvider.AWS,
        #     BucketProvider.MINIO,
        # ):
        #     msg = (
        #         f"Unsupported bucket provider {input_.bucket.bucket_provider} "
        #         f"for Dify installation."
        #         "Please contact support team describing your use-case."
        #     )
        #     raise RuntimeError(msg)
        # bucket_credentials = input_.bucket.credentials[0]
        # return {
        #     "externalS3": {
        #         "enabled": True,
        #         "endpoint": bucket_credentials.endpoint_url,
        #         "accessKey": bucket_credentials.access_key_id,
        #         "secretKey": bucket_credentials.secret_access_key,
        #         "bucketName": bucket_name,
        #     }
        # }

    async def _get_dify_pg_values(self, input_: DifyAppInputs) -> dict[str, t.Any]:
        """Get Dify values to integrate with pgvector and postgres DB"""

        postgres_values = {
            "username": input_.external_postgres.user,
            "password": input_.external_postgres.password,
            "address": input_.external_postgres.pgbouncer_host,
            "port": input_.external_postgres.pgbouncer_port,
            "dbName": input_.external_postgres.dbname,
        }
        pgvector_values = {
            "username": input_.external_pgvector.user,
            "password": input_.external_pgvector.password,
            "address": input_.external_pgvector.pgbouncer_host,
            "port": input_.external_pgvector.pgbouncer_port,
            "dbName": input_.external_pgvector.dbname,
        }

        return {
            "externalPostgres": postgres_values,
            "externalPgvector": pgvector_values,
        }

    async def _get_dify_redis_values(
        self, input_: DifyAppInputs, namespace: str, app_id: str
    ) -> dict[str, t.Any]:
        return {
            "redis": {
                "auth": {"password": secrets.token_urlsafe(16)},
                "architecture": "standalone",
                "master": await gen_extra_values(
                    self.client,
                    input_.redis.master_preset,
                    app_id=app_id,
                    namespace=namespace,
                    component_name="redis_master",
                    app_type=AppType.Dify,
                ),
            }
        }

    async def gen_extra_values(
        self,
        input_: DifyAppInputs,
        app_name: str,
        namespace: str,
        app_id: str,
        app_secrets_name: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for Dify configuration.
        """
        values = {}
        for component_name, component in [
            ("api", input_.api),
            ("worker", input_.worker),
            ("proxy", input_.proxy),
            ("web", input_.web),
        ]:
            values[component_name] = await gen_extra_values(
                self.client,
                component.preset,  # type: ignore[attr-defined]
                namespace=namespace,
                component_name=component_name,
                app_id=app_id,
                app_type=AppType.Dify,
            )

        values["api"]["secretKey"] = secrets.token_urlsafe(32)
        values["api"]["initPassword"] = secrets.token_urlsafe(16)

        values.update(await self._get_dify_pg_values(input_))
        values.update(
            await self._get_or_create_dify_blob_storage_values(input_, app_name)
        )
        values.update(await self._get_dify_redis_values(input_, namespace, app_id))
        ingress: dict[str, t.Any] = {"ingress": {}}
        if input_.ingress_http:
            http_ingress_conf = await get_http_ingress_values(
                self.client,
                input_.ingress_http,
                namespace,
                app_id,
                app_type=AppType.Dify,
            )
            ingress["ingress"] = http_ingress_conf

        return {**ingress, **values}
