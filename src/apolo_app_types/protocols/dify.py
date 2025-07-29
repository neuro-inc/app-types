from pydantic import BaseModel, ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppInputsDeployer,
    AppOutputs,
    AppOutputsDeployer,
    IngressHttp,
    Postgres,
    Preset,
    Redis,
    RestAPI,
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.postgres import CrunchyPostgresUserCredentials


class DifyApi(AbstractAppFieldType):
    replicas: int = Field(default=1, gt=0)
    preset_name: str
    title: str


class DifyWorker(AbstractAppFieldType):
    replicas: int = Field(default=1, gt=0)
    preset_name: str


class DifyProxy(AbstractAppFieldType):
    preset_name: str


class DifyWeb(AbstractAppFieldType):
    replicas: int | None = Field(default=None, gt=0)
    preset_name: str


class DifyInputs(AppInputsDeployer):
    api: DifyApi
    worker: DifyWorker
    proxy: DifyProxy
    web: DifyWeb
    redis: Redis
    externalPostgres: Postgres  # noqa: N815
    externalPGVector: Postgres  # noqa: N815


class DifyOutputs(AppOutputsDeployer):
    internal_web_app_url: str
    internal_api_url: str
    external_api_url: str | None
    init_password: str


class DifyAppApi(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify API",
            description="Configure Dify Api.",
        ).as_json_schema_extra(),
    )
    replicas: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Replicas Count",
            description="Configure Replicas count.",
        ).as_json_schema_extra(),
    )
    preset: Preset


class DifyAppWorker(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify Worker",
            description="Configure Dify Worker.",
        ).as_json_schema_extra(),
    )
    replicas: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Replicas Count",
            description="Configure Replicas count.",
        ).as_json_schema_extra(),
    )
    preset: Preset


class DifyAppProxy(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify Proxy",
            description="Configure Dify Proxy.",
        ).as_json_schema_extra(),
    )
    preset: Preset


class DifyAppWeb(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify Web",
            description="Configure Dify Web.",
        ).as_json_schema_extra(),
    )
    replicas: int = Field(
        default=1,
        gt=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Replicas Count",
            description="Configure Replicas count.",
        ).as_json_schema_extra(),
    )
    preset: Preset


class DifyAppRedis(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify Redis",
            description="Configure Dify Redis.",
        ).as_json_schema_extra(),
    )
    master_preset: Preset = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Master Preset",
            description="Configure Master Preset.",
        ).as_json_schema_extra(),
    )


class DifyAppInputs(AppInputs):
    ingress_http: IngressHttp | None = Field(
        default_factory=lambda: IngressHttp(),
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Ingress",
            description="Define HTTP ingress configuration"
            " for exposing services over the web.",
        ).as_json_schema_extra(),
    )
    api: DifyAppApi
    worker: DifyAppWorker
    proxy: DifyAppProxy
    web: DifyAppWeb
    redis: DifyAppRedis
    # bucket: Bucket = Field(
    #     ...,
    #     json_schema_extra=SchemaExtraMetadata(
    #         title="Bucket",
    #         description="Configure Dify Blob Storage (Bucket).",
    #     ).as_json_schema_extra(),
    # )
    external_postgres: CrunchyPostgresUserCredentials
    external_pgvector: CrunchyPostgresUserCredentials


class DifySpecificOutputs(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Dify Specific Outputs",
            description="Configure Dify Specific Outputs.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    init_password: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            title="Init Password",
            description="The initial password for the Dify application.",
        ).as_json_schema_extra(),
    )


class DifyAppOutputs(AppOutputs):
    internal_web_app_url: RestAPI | None = Field(
        None,
        json_schema_extra=SchemaExtraMetadata(
            title="Internal Web App URL",
            description="The URL of the internal web app.",
        ).as_json_schema_extra(),
    )
    external_web_app_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External Web App URL",
            description="The URL of the external web app.",
        ).as_json_schema_extra(),
    )
    internal_api_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Internal API URL",
            description="The URL of the internal API.",
        ).as_json_schema_extra(),
    )
    external_api_url: RestAPI | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="External API URL",
            description="The URL of the external API.",
        ).as_json_schema_extra(),
    )
    dify_specific: DifySpecificOutputs
