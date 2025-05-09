import secrets
import typing as t

from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import gen_extra_values
from apolo_app_types.helm.apps.ingress import get_http_ingress_values
from apolo_app_types.protocols.common.buckets import BucketProvider
from apolo_app_types.protocols.dify import DifyAppInputs


class DifyChartValueProcessor(BaseChartValueProcessor[DifyAppInputs]):
    async def _get_or_create_dify_blob_storage_values(
        self, input_: DifyAppInputs
    ) -> dict[str, t.Any]:
        # dify chart supports External S3 / Azure / OSS (Alibaba)
        # Otherwise, dify needs ReadWriteMany PVC, which will be supported later
        bucket_name = input_.bucket.id

        if input_.bucket.bucket_provider not in (
            BucketProvider.AWS,
            BucketProvider.MINIO,
        ):
            msg = (
                f"Unsupported bucket provider {input_.bucket.bucket_provider} "
                f"for Dify installation."
                "Please contact support team describing your use-case."
            )
            raise RuntimeError(msg)
        bucket_credentials = input_.bucket.credentials[0]
        return {
            "externalS3": {
                "enabled": True,
                "endpoint": bucket_credentials.endpoint_url,  # type: ignore[union-attr]
                "accessKey": bucket_credentials.access_key_id,  # type: ignore[union-attr]
                "secretKey": bucket_credentials.secret_access_key,  # type: ignore[union-attr]
                "bucketName": bucket_name,
            }
        }

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
        self, input_: DifyAppInputs, namespace: str
    ) -> dict[str, t.Any]:
        return {
            "redis": {
                "auth": {"password": secrets.token_urlsafe(16)},
                "architecture": "standalone",
                "master": await gen_extra_values(
                    self.client,
                    input_.redis.master_preset,
                    namespace=namespace,
                    component_name="redis_master",
                ),
            }
        }

    async def gen_extra_values(
        self,
        input_: DifyAppInputs,
        app_name: str,
        namespace: str,
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
            )

        values["api"]["secretKey"] = secrets.token_urlsafe(32)
        values["api"]["initPassword"] = secrets.token_urlsafe(16)

        values.update(await self._get_dify_pg_values(input_))
        values.update(await self._get_or_create_dify_blob_storage_values(input_))
        values.update(await self._get_dify_redis_values(input_, namespace))
        ingress: dict[str, t.Any] = {"ingress": {}}
        if input_.ingress_http:
            http_ingress_conf = await get_http_ingress_values(
                self.client, input_.ingress_http, namespace
            )
            ingress["ingress"] = http_ingress_conf

        return {**ingress, **values}
