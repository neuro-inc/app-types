import enum

from apolo_app_types import Bucket
from apolo_app_types.protocols.common import AppInputs, AppOutputs, Preset, AppOutputsV2
from pydantic import BaseModel, Field


class PGBouncer(BaseModel):
    preset: Preset = Field(
        ...,
        description="Preset to use for the PGBouncer instance.",
        title="Preset",
    )
    replicas: int = Field(
        default=2,
        description="Number of replicas for the PGBouncer instance.",
        title="PGBouncer replicas",
    )


class PostgresSupportedVersions(enum.StrEnum):
    v12 = "12"
    v13 = "13"
    v14 = "14"
    v15 = "15"
    v16 = "16"


class PostgresDBUser(BaseModel):
    name: str = Field(
        ...,
        description="Name of the database user.",
        title="Database user name",
    )
    db_names: list[str] = Field(
        default_factory=list,
        description="Name of the database.",
        title="Database name",
    )


class Postgres(BaseModel):
    postgres_version: PostgresSupportedVersions = Field(
        default=PostgresSupportedVersions.v16,
        description="Postgres version to use.",
        title="Postgres version",
    )
    instance_replicas: int = Field(
        default=3,
        description="Number of replicas for the Postgres instance.",
        title="Postgres instance replicas",
    )
    instance_size: int = Field(
        default=1,
        description="Size of the Postgres instance.",
        title="Postgres instance size",
    )
    db_users: list[PostgresDBUser] = Field(
        default_factory=list,
        description="List of database users.",
        title="Database users",
    )


class CrunchyPostgresInputs(AppInputs):
    preset: Preset = Field(
        ...,
        description="Preset to use for the Postgres instance.",
        title="Preset",
    )
    postgres: Postgres = Field(
        ...,
        description="Postgres configuration.",
        title="Postgres",
    )
    pg_bouncer: PGBouncer = Field(
        ...,
        description="PGBouncer configuration.",
        title="PGBouncer",
    )
    backup_bucket: Bucket = Field(
        ...,
        description="Bucket to use for backups.",
        title="Backup bucket",
    )


class CrunchyPostgresUserCredentials(AppOutputs):
    user: str
    password: str
    host: str
    port: str
    pgbouncer_host: str
    pgbouncer_port: str
    dbname: str | None = None
    jdbc_uri: str | None = None
    pgbouncer_jdbc_uri: str | None = None
    pgbouncer_uri: str | None = None
    uri: str | None = None


class CrunchyPostgresOutputs(AppOutputs):
    users: list[CrunchyPostgresUserCredentials]


class PostgresOutputsV2(AppOutputsV2):
    users: list[CrunchyPostgresUserCredentials]
