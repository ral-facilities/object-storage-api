"""
Module for providing a store for managing attachments in an S3 object store.
"""

import logging

from object_storage_api.core.config import config
from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.models.attachment import AttachmentOut
from object_storage_api.schemas.attachment import AttachmentPostSchema, AttachmentPostUploadInfoSchema

logger = logging.getLogger()


class AttachmentStore:
    """
    Store for managing attachments in an S3 object store.
    """

    def create_presigned_get(self, attachment: AttachmentOut) -> str:
        """
        Generate a presigned url to share an S3 object.

        :param attachment: `AttachmentOut` model of the attachment
        :return: Presigned url to get the attachment.
        """

        logger.info(
            "Generating presigned url to get attachment with object key: %s from the object store",
            attachment.object_key,
        )

        response = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": attachment.object_key,
                "ResponseContentDisposition": f'attachment; filename="{attachment.file_name}"',
            },
            ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
        )

        return response

    def create_presigned_post(
        self, attachment_id: str, attachment: AttachmentPostSchema
    ) -> tuple[str, AttachmentPostUploadInfoSchema]:
        """
        Creates a presigned post URL for uploading an attachment file to object storage.

        :param attachment_id: ID of the attachment to generate the URL for.
        :param attachment: Attachment to generate the URL for.
        :return: Tuple with
                 - Object key of the attachment.
                 - Upload info schema containing a presigned url to upload the attachment file to and the required form
                   fields for the request.
        """
        object_key = f"attachments/{attachment.entity_id}/{attachment_id}"

        logger.info(
            "Generating a presigned URL for uploading the attachment with object key: %s to the object store",
            object_key,
        )
        presigned_post_response = s3_client.generate_presigned_post(
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=object_key,
            Fields={
                # Insert content type here so it is provided in the fields and can be used directly
                "Content-Type": "multipart/form-data"
            },
            Conditions=[
                ["content-length-range", 0, config.attachment.max_size_bytes],
                ["eq", "$Content-Type", "multipart/form-data"],
            ],
            ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
        )

        return object_key, AttachmentPostUploadInfoSchema(**presigned_post_response)
