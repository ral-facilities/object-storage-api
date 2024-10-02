"""
Module for providing a store for managing attachments in an S3 object store.
"""

import logging

from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.schemas.attachment import AttachmentPostSchema

logger = logging.getLogger()


class AttachmentStore:
    """
    Store for managing attachments in an S3 object store.
    """

    def create_presigned_url(self, attachment_id: str, attachment: AttachmentPostSchema) -> tuple[str, str]:
        """
        Creates a presigned URL for uploading an attachment file.

        :param attachment_id: ID of the attachment to generate the URL for.
        :param attachment: Attachment to generate the URL for.
        :return: Tuple with
                 - Object key of the new attachment.
                 - Presigned upload url to upload the attachment file to.
        :raises InvalidObjectIdError: If the attachment has any invalid ID's in it.
        """
        object_key = f"attachments/{attachment.entity_id}/{attachment_id}"

        logger.info("Generating a presigned URL for uploading the attachment")
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": object_key,
                # To not have a signature mismatch the content type must be assigned and any requests using it must use
                # the same type in the headers as well
                "ContentType": "multipart/form-data",
            },
            ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
        )

        return object_key, url
