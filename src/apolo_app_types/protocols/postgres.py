from __future__ import annotations

import enum
import typing as t
from typing import Literal
from urllib.parse import quote

import apolo_sdk
from pydantic import ConfigDict, Field, constr, model_validator

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    ApoloSecret,
    AppInputs,
    AppOutputs,
    AppOutputsDeployer,
    Bucket,
    Preset,
    SchemaExtraMetadata,
    SchemaMetaType,
)


POSTGRES_ADMIN_DEFAULT_USER_NAME = "postgres"


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


POSTGRES_RESOURCES_PATTERN = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"


PostgresName = constr(
    strip_whitespace=True,
    min_length=1,
    max_length=63,
    pattern=POSTGRES_RESOURCES_PATTERN,
)  # type: ignore[valid-type]


class PostgresDBUser(AbstractAppFieldType):
    name: PostgresName = Field(  # type: ignore[valid-type]
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description=(
                "Name of the database user. "
                "Must be 1-63 characters long, start and end with a lowercase letter "
                "or number, and contain only lowercase letters, numbers, or hyphens."
            ),
            title="Database user name",
        ).as_json_schema_extra(),
    )

    db_names: list[  # type: ignore[valid-type]
        PostgresName  # type: ignore[valid-type]
    ] = Field(  # type: ignore[valid-type]
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            description=(
                "List of databases this user should have access to. "
                "Databases will be created if they do not exist."
            ),
            title="Databases",
        ).as_json_schema_extra(),
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
            if user.name.lower() == POSTGRES_ADMIN_DEFAULT_USER_NAME:  # type: ignore[attr-defined]
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
    password: ApoloSecret = Field(
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
    pgbouncer_uri: ApoloSecret | None = None
    postgres_uri: ApoloSecret | None = None

    user_type: t.Literal["user"] = "user"

    async def get_jdbc_uri(self) -> str | None:
        """Get JDBC URI with credentials as query parameters.

        Fetches the password from Apolo secrets and constructs a JDBC URI with
        user and password as query parameters:
        jdbc:postgresql://host:port/database?user=username&password=password
        """
        if not self.dbname:
            return None

        # Fetch the actual password value from secrets
        async with apolo_sdk.get() as client:
            password_secret = await client.secrets.get(key=self.password.key)
            password_value = password_secret.decode()

        # URL-encode username and password to handle special characters
        user_encoded = quote(self.user, safe="")
        password_encoded = quote(password_value, safe="")

        return (
            f"jdbc:postgresql://{self.host}:{self.port}/{self.dbname}"
            f"?user={user_encoded}&password={password_encoded}"
        )

    async def get_pgbouncer_jdbc_uri(self) -> str | None:
        """Get PGBouncer JDBC URI with credentials as query parameters.

        Fetches the password from Apolo secrets and constructs a JDBC URI with
        user and password as query parameters:
        jdbc:postgresql://host:port/database?user=username&password=password
        """
        if not self.dbname:
            return None

        # Fetch the actual password value from secrets
        async with apolo_sdk.get() as client:
            password_secret = await client.secrets.get(key=self.password.key)
            password_value = password_secret.decode()

        # URL-encode username and password to handle special characters
        user_encoded = quote(self.user, safe="")
        password_encoded = quote(password_value, safe="")

        return (
            f"jdbc:postgresql://{self.pgbouncer_host}:{self.pgbouncer_port}/{self.dbname}"
            f"?user={user_encoded}&password={password_encoded}"
        )


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
