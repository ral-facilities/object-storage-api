"""
Module for providing a store for managing images in an S3 object store.
"""

import logging

from botocore.exceptions import ClientError
from fastapi import UploadFile
from pydantic import HttpUrl

from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.schemas.image import ImageGetUrlInfoSchema, ImagePostMetadataSchema

logger = logging.getLogger()


class ImageStore:
    """
    Store for managing images in an S3 object store.
    """

    def upload(self, image_id: str, image_metadata: ImagePostMetadataSchema, upload_file: UploadFile) -> str:
        """
        Uploads a given image to object storage.

        :param image_id: ID of the image being uploaded.
        :param image_metadata: Metadata of the image to be uploaded.
        :param upload_file: Upload file of the image to be uploaded.
        :return: Object key of the image.
        """
        object_key = f"images/{image_metadata.entity_id}/{image_id}"

        logger.info("Uploading image file to the object storage")
        s3_client.upload_fileobj(
            upload_file.file,
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=object_key,
            ExtraArgs={"ContentType": upload_file.content_type},
        )

        return object_key

    def create_presigned_url(self, object_key: str, file_name: str) -> HttpUrl:
        """Generate a presigned URL to share an S3 object

        :param object_key: object key of the image to generate the url for.
        :return: Image Metadata with a presigned url.
        """

        try:
            response = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": object_storage_config.bucket_name.get_secret_value(),
                    "Key": object_key,
                    "ResponseContentDisposition": 'attachment; filename="{}"'.format(file_name),
                    "ResponseContentType": "image/jpeg",
                },
                ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
            )
        except ClientError as e:
            logging.error(e)
            return None

        # The response contains the presigned URL
        return response["url"]
