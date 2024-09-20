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

    # TODO: Should probably take AttachmentOut?
    def generate_presigned_upload_url(self, attachment: AttachmentPostSchema) -> str:
        """
        Generates a presigned URL for uploading an attachment.

        :param attachment: Attachment to generate the URL for.
        """

        # Should id be entity, or rather the attachment id... - effects the order of operations
        object_name = f"attachments/{attachment.entity_id}/{attachment.file_name}"

        # TODO: Configure the expiry from config
        logger.info("Generating a presigned URL for uploading the attachment")
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": object_name,
            },
            ExpiresIn=1000,
        )
        return url
