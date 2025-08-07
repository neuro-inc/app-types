import enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types import (
    AppInputs,
    AppOutputs,
)
from apolo_app_types.protocols.common import (
    IngressHttp,
    Preset,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.ingress import AuthIngressMiddleware
from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.networking import (
    RestAPI,
)
from apolo_app_types.protocols.common.openai_compat import (
    OpenAICompatChatAPI,
    OpenAICompatEmbeddingsAPI,
)
from apolo_app_types.protocols.postgres import (
    CrunchyPostgresUserCredentials,
)


class DBTypes(enum.StrEnum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class OpenWebUISpecific(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="OpenWebUI Specific",
            description="Configure OpenWebUI additional parameters.",
        ).as_json_schema_extra(),
    )
    env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Environment Variables",
            description="List of environment variables to set in"
            " the OpenWebUI application.",
        ).as_json_schema_extra(),
    )


class SQLiteDatabase(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="SQLite Database",
            description="Use a local SQLite database for OpenWebUI.",
        ).as_json_schema_extra(),
    )
    # No additional fields needed for local SQLite database
    database_type: Literal[DBTypes.SQLITE] = Field(default=DBTypes.SQLITE)


class PostgresDatabase(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Postgres Database",
            description="Use a Postgres database for OpenWebUI.",
        ).as_json_schema_extra(),
    )
    # Use Crunchy Postgres credentials for the database
    database_type: Literal[DBTypes.POSTGRES] = Field(default=DBTypes.POSTGRES)
    credentials: CrunchyPostgresUserCredentials


class DataBaseConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Database Configuration",
            description="Configure the database for OpenWebUI.",
        ).as_json_schema_extra(),
    )
    database: SQLiteDatabase | PostgresDatabase = Field(
        default_factory=lambda: SQLiteDatabase(),
        json_schema_extra=SchemaExtraMetadata(
            title="Database Configuration",
            description="Configure the database for OpenWebUI. "
            "Choose between local SQLite or Postgres.",
        ).as_json_schema_extra(),
    )


class AdvancedNetworkConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Advanced Network Configuration",
            description="Configure advanced networking settings for OpenWebUI.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )
    ingress_middleware: AuthIngressMiddleware | None = None


class NetworkConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Network Configuration",
            description="Configure networking settings for OpenWebUI.",
        ).as_json_schema_extra(),
    )
    ingress_http: IngressHttp = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Ingress",
            description="Configure HTTP ingress settings for OpenWebUI.",
        ).as_json_schema_extra(),
    )
    advanced_networking: AdvancedNetworkConfig


class OpenWebUIAppInputs(AppInputs):
    preset: Preset
    networking_config: NetworkConfig
    database_config: DataBaseConfig
    embeddings_api: OpenAICompatEmbeddingsAPI
    llm_chat_api: OpenAICompatChatAPI
    openwebui_specific: OpenWebUISpecific = Field(
        default_factory=lambda: OpenWebUISpecific(),
    )


class OpenWebUIAppOutputs(AppOutputs):
    """
    OpenWebUI outputs:
      - internal_web_app_url
      - external_web_app_url
    """

    internal_web_app_url: RestAPI | None = None
    external_web_app_url: RestAPI | None = None
