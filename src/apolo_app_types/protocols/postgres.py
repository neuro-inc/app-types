import enum

from pydantic import ConfigDict, Field

from apolo_app_types import AppInputs, Bucket
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppOutputs,
    AppOutputsDeployer,
    Preset,
    SchemaExtraMetadata,
    SchemaMetaType,
)


class PostgresURI(AbstractAppFieldType):
    """Configuration for the Postgres connection URI."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres URI",
            description="Full Postgres connection URI configuration.",
        ).as_json_schema_extra(),
    )
    uri: str | None = Field(
        default=None,
        description=(
            "Full Postgres connection URI. E.g. 'postgresql://user:pass@host:5432/db'"
        ),
        title="URI",
    )


class PGBouncer(AbstractAppFieldType):
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


class PostgresDBUser(AbstractAppFieldType):
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


class PostgresConfig(AbstractAppFieldType):
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


class PostgresInputs(AppInputs):
    preset: Preset
    postgres_config: PostgresConfig
    pg_bouncer: PGBouncer
    backup_bucket: Bucket


class CrunchyPostgresUserCredentials(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres User Credentials",
            description="Configuration for Crunchy Postgres user credentials.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    user: str
    password: str
    host: str
    port: int
    pgbouncer_host: str
    pgbouncer_port: int
    dbname: str | None = None
    jdbc_uri: str | None = None
    pgbouncer_jdbc_uri: str | None = None
    pgbouncer_uri: str | None = None
    uri: str | None = None
    postgres_uri: PostgresURI | None = None


class CrunchyPostgresOutputs(AppOutputsDeployer):
    users: list[CrunchyPostgresUserCredentials]


class PostgresUsers(AbstractAppFieldType):
    users: list[CrunchyPostgresUserCredentials]


class PostgresOutputs(AppOutputs):
    postgres_users: PostgresUsers | None = None
