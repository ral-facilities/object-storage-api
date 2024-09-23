"""
Module for providing a store for managing attachments in an S3 object store.
"""

import logging

from bson import ObjectId

from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.models.attachment import AttachmentIn
from object_storage_api.schemas.attachment import AttachmentPostSchema

logger = logging.getLogger()


class AttachmentStore:
    """
    Store for managing attachments in an S3 object store.
    """

    def generate_presigned_upload_url(self, attachment: AttachmentPostSchema) -> tuple[AttachmentIn, str]:
        """
        Generates a presigned URL for uploading an attachment.

        :param attachment: Attachment to generate the URL for.
        :return: Tuple with
                 - Attachment model to insert into the database (includes its location in the object storage).
                 - Presigned upload url to upload the attachment file to.
        """

        # Generate a unique ID for the attachment - this needs to be known now to avoid inserting into the database
        # before generating the presigned URL which would then require transactions
        attachment_id = str(ObjectId())

        object_key = f"attachments/{attachment.entity_id}/{attachment_id}"

        logger.info("Generating a presigned URL for uploading the attachment")
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": object_key,
            },
            ExpiresIn=object_storage_config.presigned_url_expiry,
        )
        return AttachmentIn(**attachment.model_dump(), id=attachment_id, object_key=object_key), url
