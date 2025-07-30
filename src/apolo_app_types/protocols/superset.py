from pydantic import ConfigDict, Field

from apolo_app_types import CrunchyPostgresUserCredentials
from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppOutputs,
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
    ServiceAPI,
)
from apolo_app_types.protocols.common.networking import HttpApi


class WebConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Web Configuration",
            description=("Set the configuration for Superset Web UI."),
        ).as_json_schema_extra(),
    )
    preset: Preset


class WorkerConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Worker Configuration",
            description=("Set the configuration for Superset worker."),
        ).as_json_schema_extra(),
    )
    preset: Preset


class SupersetUserConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Configuration for the admin user.",
            description="Set the admin user fields to be ",
        ).as_json_schema_extra(),
    )
    username: str = Field(
        default="admin",
        json_schema_extra=SchemaExtraMetadata(
            title="Admin Username", description="Set Admin Username."
        ).as_json_schema_extra(),
    )
    firstname: str = Field(
        default="Superset",
        json_schema_extra=SchemaExtraMetadata(
            title="Admin Firstname", description="Set Admin first name."
        ).as_json_schema_extra(),
    )
    lastname: str = Field(
        default="Admin",
        json_schema_extra=SchemaExtraMetadata(
            title="Admin Lastname", description="Set Admin last name."
        ).as_json_schema_extra(),
    )
    email: str = Field(
        default="admin@superset.com",
        json_schema_extra=SchemaExtraMetadata(
            title="Admin Email", description="Set Admin email."
        ).as_json_schema_extra(),
    )
    password: str = Field(
        default="admin",
        json_schema_extra=SchemaExtraMetadata(
            title="Admin Password", description="Set Admin password."
        ).as_json_schema_extra(),
    )


class SupersetPostgresConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Superset Postgres.",
            description="Set the configuration for the superset database.",
        ).as_json_schema_extra(),
    )
    preset: Preset


class SupersetInputs(AppInputs):
    ingress_http: IngressHttp

    worker_config: WorkerConfig
    web_config: WebConfig
    redis_preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Redis Preset",
            description="Set the Redis preset for Superset.",
        ).as_json_schema_extra(),
    )
    postgres_config: CrunchyPostgresUserCredentials | SupersetPostgresConfig = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres Configuration",
            description=(
                "Set your own postgres as a database for Superset app. "
                "If it was not provided, "
                "postgres instance will be created within the same app."
            ),
        ).as_json_schema_extra(),
    )
    admin_user: SupersetUserConfig = Field(default_factory=lambda: SupersetUserConfig())


class SupersetOutputs(AppOutputs):
    web_app_url: ServiceAPI[HttpApi] = Field(
        default=ServiceAPI[HttpApi](),
        json_schema_extra=SchemaExtraMetadata(
            title="Superset Web App URL",
            description=("URL to access the Superset web application. "),
        ).as_json_schema_extra(),
    )
    secret: str | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Superset Secret",
            description=("Secret token for Superset."),
        ).as_json_schema_extra(),
    )
    admin_user: SupersetUserConfig | None = None
