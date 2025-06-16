# pyright: ignore
import enum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.schema_extra import (
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.secrets_ import ApoloSecret


class CredentialsType(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"


class BucketCredentials(AbstractAppFieldType):
    type: CredentialsType = Field(
        CredentialsType.READ_ONLY,
        json_schema_extra=SchemaExtraMetadata(
            description="The type of the bucket.",
            title="Bucket type",
        ).as_json_schema_extra(),
    )


class GCPBucketCredentials(BucketCredentials):
    key_data: ApoloSecret = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The key data of the bucket.",
            title="Bucket key data",
        ).as_json_schema_extra(),
    )


class MinioBucketCredentials(BucketCredentials):
    endpoint_url: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The endpoint URL of the bucket.",
            title="Bucket endpoint URL",
        ).as_json_schema_extra(),
    )
    region_name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The region name of the bucket.",
            title="Bucket region name",
        ).as_json_schema_extra(),
    )
    access_key_id: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The access key ID of the bucket.",
            title="Bucket access key ID",
        ).as_json_schema_extra(),
    )
    secret_access_key: ApoloSecret = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The secret access key of the bucket.",
            title="Bucket secret access key",
        ).as_json_schema_extra(),
    )


class S3BucketCredentials(BucketCredentials):
    region_name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The region name of the bucket.",
            title="Bucket region name",
        ).as_json_schema_extra(),
    )
    endpoint_url: str | None = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The endpoint URL of the bucket.",
            title="Bucket endpoint URL",
        ).as_json_schema_extra(),
    )
    access_key_id: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The access key ID of the bucket.",
            title="Bucket access key ID",
        ).as_json_schema_extra(),
    )
    secret_access_key: ApoloSecret = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The secret access key of the bucket.",
            title="Bucket secret access key",
        ).as_json_schema_extra(),
    )


class BucketProvider(str, enum.Enum):
    AWS = "AWS"
    MINIO = "MINIO"
    GCP = "GCP"
    AZURE = "AZURE"
    OPEN_STACK = "OPEN_STACK"


class Bucket(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Bucket",
            description="Configuration for Bucket.",
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )
    id: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The bucket ID.",
            title="Bucket ID",
        ).as_json_schema_extra(),
    )
    name: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The name of the bucket.",
            title="Bucket name",
        ).as_json_schema_extra(),
    )
    owner: str = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The owner of the bucket.",
            title="Bucket owner",
        ).as_json_schema_extra(),
    )
    details: dict[str, str] = Field(
        default_factory=dict,
        json_schema_extra=SchemaExtraMetadata(
            description="The details of the bucket.",
            title="Bucket details",
        ).as_json_schema_extra(),
    )
    credentials: list[
        S3BucketCredentials | MinioBucketCredentials | GCPBucketCredentials
    ] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            description="The credentials of the bucket.",
            title="Bucket credentials",
        ).as_json_schema_extra(),
    )
    bucket_provider: BucketProvider = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="The provider of the bucket.",
            title="Bucket provider",
        ).as_json_schema_extra(),
    )
