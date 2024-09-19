import boto3

from object_storage_api.core.config import config

object_storage_config = config.object_storage
s3_client = boto3.client(
    "s3",
    endpoint_url=object_storage_config.endpoint_url.get_secret_value(),
    aws_access_key_id=object_storage_config.access_key.get_secret_value(),
    aws_secret_access_key=object_storage_config.secret_access_key.get_secret_value(),
)
