from typing import Annotated, Generic, Literal, TypeVar

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common.abc_ import AbstractAppFieldType
from apolo_app_types.protocols.common.buckets import (
    BucketProvider,
    GCPBucketCredentials,
    MinioBucketCredentials,
    S3BucketCredentials,
)
from apolo_app_types.protocols.common.schema_extra import SchemaExtraMetadata


S3Schema = Annotated[str, Field(pattern=r"^s3://")]
GCSchema = Annotated[str, Field(pattern=r"^gs://")]
Miniochema = Annotated[str, Field(pattern=r"^minio://")]

BucketSchema = TypeVar("BucketSchema", S3Schema, GCSchema, Miniochema)


class ListOfBuckets(AbstractAppFieldType, Generic[BucketSchema]):
    model_config = ConfigDict(
        json_schema_extra=SchemaExtraMetadata(
            title="List of buckets",
            description="List all buckets to be connected to Apolo. "
            "If no bucket is provided, the account used "
            "to connect to the bucket provider must have access to "
            "list all buckets.",
        ).as_json_schema_extra()
    )
    buckets: list[BucketSchema] = Field(
        default_factory=list,
    )


class AwsS3(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="AWS S3",
            description="Configure your AWS S3 App.",
        ).as_json_schema_extra(),
    )
    provider: Literal[BucketProvider.AWS]
    list_of_buckets: ListOfBuckets[S3Schema]
    credentials: S3BucketCredentials = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Credentials for the AWS S3 bucket.",
            title="Credentials",
        ).as_json_schema_extra(),
    )


class GCPBucket(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Google Cloud Storage",
            description="Configure your GCS App.",
        ).as_json_schema_extra(),
    )
    provider: Literal[BucketProvider.GCP]
    list_of_buckets: ListOfBuckets[GCSchema]
    credentials: GCPBucketCredentials = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Credentials for the Google Cloud Storage bucket.",
            title="Credentials",
        ).as_json_schema_extra(),
    )


class MinioBucket(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="MinIO",
            description="Configure your MinIO App.",
        ).as_json_schema_extra(),
    )
    provider: Literal[BucketProvider.MINIO]
    list_of_buckets: ListOfBuckets[Miniochema]
    credentials: MinioBucketCredentials = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Credentials for the MinIO bucket.",
            title="Credentials",
        ).as_json_schema_extra(),
    )


bucket_types = AwsS3 | GCPBucket | MinioBucket


class BucketConfig(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Bucket App Configuration",
            description="Choose the bucket provider and configure the credentials.",
        ).as_json_schema_extra(),
    )
    bucket_provider: bucket_types = Field(
        ...,
        json_schema_extra=SchemaExtraMetadata(
            description="Provider of the bucket service.",
            title="Bucket Provider",
        ).as_json_schema_extra(),
    )


class BucketsAppInputs(AbstractAppFieldType):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="AWS S3 App Inputs",
            description="Configure the your AWS S3 App.",
        ).as_json_schema_extra(),
    )
    bucket_config: BucketConfig
