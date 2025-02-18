"""
Module for providing a store for managing images in an S3 object store.
"""

import logging

from fastapi import UploadFile

from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.models.image import ImageOut
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

        logger.info("Uploading image file with object key: %s to the object store", object_key)
        s3_client.upload_fileobj(
            upload_file.file,
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=object_key,
            ExtraArgs={"ContentType": upload_file.content_type},
        )

        return object_key

    def create_presigned_get(self, image: ImageOut) -> tuple[str, str]:
        """
        Generate a presigned URL to share an S3 object.

        :param image: `ImageOut` model of the image.
        :return: Presigned urls to view and download the image.
        """
        logger.info("Generating presigned url to get image with object key: %s from the object store", image.object_key)

        parameters = {
            "ClientMethod": "get_object",
            "Params": {
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": image.object_key,
                "ResponseContentDisposition": f'inline; filename="{image.file_name}"',
            },
            "ExpiresIn": object_storage_config.presigned_url_expiry_seconds,
        }

        view_url = s3_client.generate_presigned_url(**parameters)

        download_url = s3_client.generate_presigned_url(
            **{
                **parameters,
                "Params": {
                    **parameters["Params"],
                    "ResponseContentDisposition": f'attachment; filename="{image.file_name}"',
                },
            }
        )

        return view_url, download_url

    def delete(self, object_key: str) -> None:
        """
        Deletes a given image from object storage.

        :param object_key: Key of the image to delete.
        """

        logger.info("Deleting image file with object key: %s from the object store", object_key)
        s3_client.delete_object(
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=object_key,
        )

    def delete_many(self, object_keys: list[str]) -> None:
        """
        Deletes given images from object storage by object keys.

        It does this in batches due to the `delete_objects` request only allowing a list of up to 1000 keys.

        :param object_keys: Keys of the images to delete.
        """
        logger.info("Deleting image files with object keys: %s from the object store", object_keys)

        # There is some duplicate code here, due to the attachments and images methods being very similar
        # pylint: disable=duplicate-code

        batch_size = 1000
        # Loop through the list of object keys in steps of `batch_size`
        for i in range(0, len(object_keys), batch_size):
            batch = object_keys[i : i + batch_size]
            s3_client.delete_objects(
                Bucket=object_storage_config.bucket_name.get_secret_value(),
                Delete={"Objects": [{"Key": key} for key in batch]},
            )

        # pylint: enable=duplicate-code
