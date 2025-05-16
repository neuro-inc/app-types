import logging

import apolo_sdk


logger = logging.getLogger(__name__)


async def get_or_create_bucket_credentials(
    *,
    client: apolo_sdk.Client,
    bucket_name: str,
    credentials_name: str,
    supported_providers: list[apolo_sdk.Bucket.Provider],
) -> apolo_sdk.PersistentBucketCredentials:
    bucket_created = False
    try:
        bucket = await client.buckets.get(bucket_id_or_name=bucket_name)
        logger.info(
            "Found existing bucket %s, using it as a backup target", bucket_name
        )
    except apolo_sdk.ResourceNotFound:
        bucket = await client.buckets.create(name=bucket_name)
        logger.info("Created new bucket %s for backups", bucket_name)
        bucket_created = True
    if supported_providers and bucket.provider not in supported_providers:
        if bucket_created:
            await client.buckets.rm(bucket_id_or_name=bucket.id)
        error = f"Unsupported bucket provider {bucket.provider.name}"
        raise ValueError(error)
    try:
        bucket_credentials = await client.buckets.persistent_credentials_get(
            credential_id_or_name=credentials_name,
        )
        logger.info("Found existing bucket credentials %s", credentials_name)
    except apolo_sdk.ResourceNotFound:
        bucket_credentials = await client.buckets.persistent_credentials_create(
            bucket_ids=[bucket.id],
            name=credentials_name,
            read_only=False,
        )
        logger.info("Created new bucket credentials %s", credentials_name)

    # bucket_credentials.credentials[0].credentials
    # AWS/MINIO: {
    #   bucket_name: str
    #   endpoint_url: str
    #   region_name: str
    #   access_key_id: str
    #   secret_access_key: str
    # }
    # GCP: {
    #   bucket_name: str
    #   key_data: base64 encoded json
    # }
    # Azure: need to check :)
    return bucket_credentials
