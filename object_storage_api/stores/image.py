"""
Module for providing a store for managing images in an S3 object store.
"""

import logging

from fastapi import UploadFile

from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.schemas.image import ImagePostMetadataSchema

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

    def delete(self, object_key: str) -> None:
        res = s3_client.delete_object(
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=object_key,
        )

        print(res)

        response = s3_client.delete_object(
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key="images/14295f7n1029435f7h3201945h/asdfu7u9081v23g4578gh1",
        )

        print(response)
