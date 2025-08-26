from __future__ import annotations

import enum
import typing as t
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from apolo_app_types import AppInputs, Bucket
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppOutputs,
    AppOutputsDeployer,
    Preset,
    SchemaExtraMetadata,
    SchemaMetaType,
)


POSTGRES_ADMIN_DEFAULT_USER_NAME = "postgres"


class PostgresURI(AbstractAppFieldType):
    """Configuration for the Postgres connection URI."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres URI",
            description="Full Postgres connection URI configuration.",
        ).as_json_schema_extra(),
    )
    uri: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="URI",
            description=(
                "Specify full Postgres connection URI. E.g. 'postgresql://user:pass@host:5432/db'"
            ),
        ).as_json_schema_extra(),
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
        gt=0,
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
        json_schema_extra=SchemaExtraMetadata(
            description="Set version of the Postgres server to use.",
            title="Postgres version",
        ).as_json_schema_extra(),
    )
    instance_replicas: int = Field(
        default=3,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            description="Set number of replicas for the Postgres instance.",
            title="Postgres instance replicas",
        ).as_json_schema_extra(),
    )
    instance_size: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            description="Set size of the Postgres instance disk (in GB).",
            title="Postgres instance disk size",
        ).as_json_schema_extra(),
    )
    db_users: list[PostgresDBUser] = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description=(
                "Configure list of users and databases they have access to. "
                "Multiple users could have access to the same database."
                "Postgres user 'postgres' is always created and has access "
                "to all databases."
            ),
            title="Database users",
        ).as_json_schema_extra(),
        min_length=1,
    )

    @model_validator(mode="after")
    def check_db_users_not_empty(self) -> PostgresConfig:
        if not self.db_users:
            err_msg = "Database Users list must not be empty."
            raise ValueError(err_msg)

        for user in self.db_users:
            if user.name.lower() == POSTGRES_ADMIN_DEFAULT_USER_NAME:
                err_msg = (
                    f"User name '{POSTGRES_ADMIN_DEFAULT_USER_NAME}'"
                    f" is reserved and this user will be created automatically."
                )
                raise ValueError(err_msg)
        return self


class PGBackupConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Enable Backups",
            description="Enable backup for your Postgres cluster.",
        ).as_json_schema_extra(),
    )
    enable: Literal[True] = Field(
        default=True,
        title="Enable backups",
        description=(
            "Enable backups for the Postgres cluster. "
            "We automatically create and configure the corresponding backup "
            "bucket for you. "
            "Note: this bucket will not be automatically removed when you remove "
            "the app."
        ),
    )
    backup_bucket: Bucket | None = Field(
        default=None,
        title="Custom backup bucket",
        description=(
            "Optionally provide your own bucket for backups. "
            "If not provided, a default bucket will be created."
        ),
    )


class PostgresInputs(AppInputs):
    preset: Preset
    postgres_config: PostgresConfig
    pg_bouncer: PGBouncer
    backup: PGBackupConfig | None = None


class BasePostgresUserCredentials(AbstractAppFieldType):
    """Base class for Postgres user credentials."""

    user: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Username for the Postgres user.",
            title="Postgres User",
        ).as_json_schema_extra(),
    )
    password: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Password for the Postgres user.",
            title="Postgres Password",
        ).as_json_schema_extra(),
    )
    host: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Host of the Postgres instance.",
            title="Postgres Host",
        ).as_json_schema_extra(),
    )
    port: int = Field(
        ...,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            description="Port of the Postgres instance.",
            title="Postgres Port",
        ).as_json_schema_extra(),
    )
    pgbouncer_host: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Host of the PGBouncer instance.",
            title="PGBouncer Host",
        ).as_json_schema_extra(),
    )
    pgbouncer_port: int = Field(
        default=...,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            description="Port of the PGBouncer instance.",
            title="PGBouncer Port",
        ).as_json_schema_extra(),
    )


class CrunchyPostgresUserCredentials(BasePostgresUserCredentials):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres User Credentials",
            description="Configuration for Crunchy Postgres user credentials.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    dbname: str | None = None
    jdbc_uri: str | None = None
    pgbouncer_jdbc_uri: str | None = None
    pgbouncer_uri: str | None = None
    uri: str | None = None
    postgres_uri: PostgresURI | None = None

    def with_database(self, database: str) -> CrunchyPostgresUserCredentials:
        updates: dict[str, t.Any] = {
            "dbname": database,
        }
        if self.jdbc_uri:
            updates["jdbc_uri"] = self.jdbc_uri.replace(
                f"/{self.dbname}", f"/{database}"
            )
        if self.pgbouncer_jdbc_uri:
            updates["pgbouncer_jdbc_uri"] = self.pgbouncer_jdbc_uri.replace(
                f"/{self.dbname}", f"/{database}"
            )
        if self.pgbouncer_uri:
            updates["pgbouncer_uri"] = self.pgbouncer_uri.replace(
                f"/{self.dbname}", f"/{database}"
            )
        if self.uri:
            updates["uri"] = self.uri.replace(f"/{self.dbname}", f"/{database}")
        if self.postgres_uri:
            uri = self.postgres_uri.uri or ""
            uri = uri.replace(f"/{self.dbname}", f"/{database}")
            updates["postgres_uri"] = PostgresURI(uri=uri)
        return self.model_copy(update=updates)

    user_type: t.Literal["user"] = "user"


class PostgresAdminUser(BasePostgresUserCredentials):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres Admin User",
            description="Configuration for the Postgres admin user.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    user_type: t.Literal["admin"] = "admin"


class CrunchyPostgresOutputs(AppOutputsDeployer):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Crunchy Postgres Outputs",
            description="Outputs for Crunchy Postgres app.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    users: list[CrunchyPostgresUserCredentials]


class PostgresUsers(AbstractAppFieldType):
    postgres_admin_user: PostgresAdminUser | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres Admin User",
            description="Admin user for the Postgres instance.",
        ).as_json_schema_extra(),
    )
    users: list[CrunchyPostgresUserCredentials] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres Users",
            description="List of Postgres users with their credentials.",
        ).as_json_schema_extra(),
    )


class PostgresOutputs(AppOutputs):
    postgres_users: PostgresUsers | None = None
