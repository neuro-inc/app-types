import typing as t

from apolo_app_types import Bucket
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.helm.apps.common import (
    get_preset,
    preset_to_affinity,
    preset_to_resources,
    preset_to_tolerations,
)
from apolo_app_types.helm.utils.deep_merging import merge_list_of_dicts
from apolo_app_types.protocols.common.buckets import (
    BucketProvider,
    GCPBucketCredentials,
    MinioBucketCredentials,
    S3BucketCredentials,
)
from apolo_app_types.protocols.common.secrets_ import serialize_optional_secret
from apolo_app_types.protocols.postgres import PostgresDBUser, PostgresInputs


class PostgresValueProcessor(BaseChartValueProcessor[PostgresInputs]):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def gen_extra_helm_args(self, *_: t.Any) -> list[str]:
        return ["--timeout", "30m"]

    def _gen_instances_config(
        self,
        instance_preset_name: str,
        instance_replicas: int,
        instances_size: int,
    ) -> list[dict[str, t.Any]]:
        preset = get_preset(self.client, instance_preset_name)
        resources = preset_to_resources(preset)
        tolerations = preset_to_tolerations(preset)
        affinity = preset_to_affinity(preset)

        pod_anti_afinity = {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 100,
                    "podAffinityTerm": {
                        "topologyKey": "kubernetes.io/hostname",
                        "labelSelector": {
                            "matchExpressions": [
                                {
                                    "key": "platform.apolo.us/component",
                                    "operator": "In",
                                    "values": ["app"],
                                },
                                {
                                    "key": "platform.apolo.us/app",
                                    "operator": "In",
                                    "values": ["crunchypostgresql"],
                                },
                            ]
                        },
                    },
                }
            ]
        }
        affinity["podAntiAffinity"] = pod_anti_afinity

        instance = {
            "name": "instance1",
            "metadata": {
                "labels": {
                    "platform.apolo.us/component": "app",
                    "platform.apolo.us/app": "crunchypostgresql",
                    "platform.apolo.us/preset": instance_preset_name,
                },
            },
            "replicas": int(instance_replicas),
            "dataVolumeClaimSpec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": f"{instances_size}Gi"}},
            },
            "resources": resources,
            "tolerations": tolerations,
            "affinity": affinity,
        }
        return [instance]

    def _create_users_config(
        self, db_users: list[PostgresDBUser]
    ) -> list[dict[str, t.Any]]:
        # Set user[].password to "AlphaNumeric" since often non-alphanumberic
        # characters break client libs :(
        users_config: list[dict[str, t.Any]] = [{"name": "postgres"}]
        for db_user in db_users:
            users_config.append(
                {
                    "name": db_user.name,
                    "password": {"type": "AlphaNumeric"},
                }
            )
        return users_config

    def _get_bouncer_config(
        self,
        bouncer_preset_name: str,
        bouncer_repicas: int,
    ) -> dict[str, t.Any]:
        preset = get_preset(self.client, bouncer_preset_name)
        resources = preset_to_resources(preset)
        tolerations = preset_to_tolerations(preset)
        affinity = preset_to_affinity(preset)
        pod_anti_afinity = {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 100,
                    "podAffinityTerm": {
                        "topologyKey": "kubernetes.io/hostname",
                        "labelSelector": {
                            "matchExpressions": [
                                {
                                    "key": "platform.apolo.us/component",
                                    "operator": "In",
                                    "values": ["app"],
                                },
                                {
                                    "key": "platform.apolo.us/app",
                                    "operator": "In",
                                    "values": ["crunchypostgresql"],
                                },
                            ]
                        },
                    },
                }
            ]
        }

        affinity["podAntiAffinity"] = pod_anti_afinity

        return {
            "affinity": affinity,
            "metadata": {
                "labels": {
                    "platform.apolo.us/component": "app",
                    "platform.apolo.us/app": "crunchypostgresql",
                    "platform.apolo.us/preset": bouncer_preset_name,
                },
            },
            "replicas": bouncer_repicas,
            "resources": resources,
            "tolerations": tolerations,
        }

    def _get_backup_config(
        self, bucket: Bucket, app_secrets_name: str
    ) -> dict[str, t.Any]:
        if bucket.bucket_provider in (
            BucketProvider.MINIO,
            BucketProvider.AWS,
        ):
            s3_like_bucket_creds: S3BucketCredentials | MinioBucketCredentials = (
                bucket.credentials[0]  # type: ignore
            )

            backup_config = {
                "bucket": bucket.id,
                "endpoint": s3_like_bucket_creds.endpoint_url,
                "region": s3_like_bucket_creds.region_name,
                "key": serialize_optional_secret(
                    s3_like_bucket_creds.access_key_id, secret_name=app_secrets_name
                ),
                "keySecret": serialize_optional_secret(
                    s3_like_bucket_creds.secret_access_key, secret_name=app_secrets_name
                ),
            }
            return {"s3": backup_config}
        if bucket.bucket_provider == BucketProvider.GCP:
            bucket_creds: GCPBucketCredentials = bucket.credentials[0]  # type: ignore
            key = serialize_optional_secret(
                bucket_creds.key_data, secret_name=app_secrets_name
            )
            backup_config = {
                "bucket": bucket.id,
                "key": key,
            }
            return {"gcs": backup_config}
        # For Azure, we need to return a bit more data from API
        exception_description = f"Unsupported bucket provider: {bucket.bucket_provider}"
        raise ValueError(exception_description)

    async def gen_extra_values(
        self,
        input_: PostgresInputs,
        app_name: str,
        namespace: str,
        app_secrets_name: str,
        *_: t.Any,
        **kwargs: t.Any,
    ) -> dict[str, t.Any]:
        """
        Generate extra Helm values for postgres configuration.
        """
        instances = self._gen_instances_config(
            instance_preset_name=input_.preset.name,
            instance_replicas=input_.postgres_config.instance_replicas,
            instances_size=input_.postgres_config.instance_size,
        )

        bouncer_preset_name = input_.pg_bouncer.preset.name
        pgbouncer_config = {}
        if bouncer_preset_name:
            pgbouncer_config = self._get_bouncer_config(
                bouncer_preset_name=bouncer_preset_name,
                bouncer_repicas=int(input_.pg_bouncer.replicas),
            )

        values: dict[str, t.Any] = {
            "metadata": {"labels": {"platform.apolo.us/component": "app"}},
            "features": {
                "AutoCreateUserSchema": "true",
            },
        }
        users_config = self._create_users_config(input_.postgres_config.db_users)

        if instances:
            values["instances"] = instances
        if pgbouncer_config:
            values["pgBouncerConfig"] = pgbouncer_config
        if users_config:
            values["users"] = users_config

        backup_config = self._get_backup_config(input_.backup_bucket, app_secrets_name)

        return merge_list_of_dicts([backup_config, values])
