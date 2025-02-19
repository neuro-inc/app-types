import enum

from pydantic import BaseModel, Field, field_validator


class CredentialsType(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"


class BucketCredentials(BaseModel):
    name: str = Field(
        ...,
        description="The name of the bucket.",
        title="Bucket name",
    )
    type: CredentialsType = Field(
        CredentialsType.READ_ONLY,
        description="The type of the bucket.",
        title="Bucket type",
    )


class GCPBucketCredentials(BucketCredentials):
    key_data: str = Field(
        ...,
        description="The key data of the bucket.",
        title="Bucket key data",
    )


class MinioBucketCredentials(BucketCredentials):
    access_key_id: str = Field(
        ...,
        description="The access key ID of the bucket.",
        title="Bucket access key ID",
    )
    secret_access_key: str = Field(
        ...,
        description="The secret access key of the bucket.",
        title="Bucket secret access key",
    )
    endpoint_url: str = Field(
        ...,
        description="The endpoint URL of the bucket.",
        title="Bucket endpoint URL",
    )
    region_name: str = Field(
        ...,
        description="The region name of the bucket.",
        title="Bucket region name",
    )


class S3BucketCredentials(BucketCredentials):
    access_key_id: str = Field(
        ...,
        description="The access key ID of the bucket.",
        title="Bucket access key ID",
    )
    secret_access_key: str = Field(
        ...,
        description="The secret access key of the bucket.",
        title="Bucket secret access key",
    )
    endpoint_url: str = Field(
        ...,
        description="The endpoint URL of the bucket.",
        title="Bucket endpoint URL",
    )
    region_name: str = Field(
        ...,
        description="The region name of the bucket.",
        title="Bucket region name",
    )


class BucketProvider(str, enum.Enum):
    AWS = "AWS"
    MINIO = "MINIO"
    GCP = "GCP"
    AZURE = "AZURE"
    OPEN_STACK = "OPEN_STACK"


class Bucket(BaseModel):
    id: str = Field(
        ...,
        description="The bucket ID.",
        title="Bucket ID",
    )
    owner: str = Field(
        ...,
        description="The owner of the bucket.",
        title="Bucket owner",
    )
    details: dict[str, str] = Field(
        default_factory=dict,
        description="The details of the bucket.",
        title="Bucket details",
    )
    credentials: list[S3BucketCredentials | MinioBucketCredentials | GCPBucketCredentials] = Field(
        default_factory=list,
        description="The credentials of the bucket.",
        title="Bucket credentials",
    )
    bucket_provider: BucketProvider = Field(
        ...,
        description="The provider of the bucket.",
        title="Bucket provider",
    )

    @field_validator("credentials", mode="before")
    @classmethod
    def validate_credentials(cls, value, values):
        provider = values.get("bucket_provider")
        if provider:
            provider_mapping = {
                BucketProvider.AWS: S3BucketCredentials,
                BucketProvider.MINIO: MinioBucketCredentials,
                BucketProvider.GCP: GCPBucketCredentials,
            }
            expected_model = provider_mapping.get(provider)
            if expected_model and not isinstance(value, expected_model):
                raise ValueError(f"Credentials must be of type {expected_model.__name__} for provider {provider}")
        return value