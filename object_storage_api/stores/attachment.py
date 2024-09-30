"""
Module for providing a store for managing attachments in an S3 object store.
"""

import logging

from bson import ObjectId

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.models.attachment import AttachmentIn
from object_storage_api.schemas.attachment import AttachmentPostSchema, AttachmentPostUploadInfoSchema

logger = logging.getLogger()


class AttachmentStore:
    """
    Store for managing attachments in an S3 object store.
    """

    def create(self, attachment: AttachmentPostSchema) -> tuple[AttachmentIn, AttachmentPostUploadInfoSchema]:
        """
        Creates an `AttachmentIn` database model with the file object key and generates a presigned URL for uploading
        it.

        :param attachment: Attachment to generate the URL for.
        :return: Tuple with
                 - Attachment model to insert into the database (includes its location in the object storage).
                 - Upload info schema containing a presigned url to upload the attachment file to and the required form
                   fields for the request.
        :raises InvalidObjectIdError: If the attachment has any invalid ID's in it.
        """

        # Generate a unique ID for the attachment - this needs to be known now to avoid inserting into the database
        # before generating the presigned URL which would then require transactions
        attachment_id = str(ObjectId())

        object_key = f"attachments/{attachment.entity_id}/{attachment_id}"

        logger.info("Generating a presigned URL for uploading the attachment")
        presigned_post_response = s3_client.generate_presigned_post(
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=object_key,
            Fields={
                # Insert content type here so it is provided in the fields and can be used directly
                "Content-Type": "multipart/form-data"
            },
            Conditions=[
                ["content-length-range", 0, object_storage_config.attachment_max_size_bytes],
                ["eq", "$Content-Type", "multipart/form-data"],
            ],
            ExpiresIn=object_storage_config.presigned_url_expiry,
        )

        try:
            attachment_in = AttachmentIn(**attachment.model_dump(), id=attachment_id, object_key=object_key)
        except InvalidObjectIdError as exc:
            # Provide more specific detail
            exc.response_detail = "Invalid `entity_id` given"
            raise exc

        return attachment_in, AttachmentPostUploadInfoSchema(**presigned_post_response)
