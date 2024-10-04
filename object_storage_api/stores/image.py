"""
Module for providing a store for managing images in an S3 object store.
"""

import logging

from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.schemas.image import ImagePostSchema

logger = logging.getLogger()


class ImageStore:
    """
    Store for managing images in an S3 object store.
    """

    def upload_image(self, image_id: str, image: ImagePostSchema) -> str:
        """
        Uploads a given image to object storage.

        :param attachment_id: ID of the attachment to generate the URL for.
        :param attachment: Attachment to generate the URL for.
        :return: Object key of the image.
        """
        object_key = f"images/{image.entity_id}/{image_id}"

        logger.info("Uploading image file to the object storage")
        s3_client.upload_fileobj(
            image.upload_file.file, Bucket=object_storage_config.bucket_name.get_secret_value(), Key=object_key
        )

        return object_key
