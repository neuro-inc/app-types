import enum

from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types import AppInputs, Bucket
from apolo_app_types.protocols.common import (
    AppOutputs,
    AppOutputsDeployer,
    Preset,
    SchemaExtraMetadata,
)


class PGBouncer(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="PG Bouncer",
            description="Configuration for PG Bouncer.",
        ).as_json_schema_extra(),
    )
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


class PostgresConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres",
            description="Configuration for Postgres.",
        ).as_json_schema_extra(),
    )
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
        description="Size of the Postgres instance disk.",
        title="Postgres instance disk size",
    )
    db_users: list[PostgresDBUser] = Field(
        default_factory=list,
        description="List of database users.",
        title="Database users",
    )


class CrunchyPostgresInputs(AppInputs):
    preset: Preset
    postgres_config: PostgresConfig
    pg_bouncer: PGBouncer
    backup_bucket: Bucket


class CrunchyPostgresUserCredentials(BaseModel):
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


class CrunchyPostgresOutputs(AppOutputsDeployer):
    users: list[CrunchyPostgresUserCredentials]


class PostgresUsers(BaseModel):
    users: list[CrunchyPostgresUserCredentials]


class PostgresOutputsV2(AppOutputs):
    postgres_users: PostgresUsers | None = None
