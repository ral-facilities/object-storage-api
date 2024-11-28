"""
Module for providing a service for managing attachments using the `AttachmentRepo` repository and `AttachmentStore`
store.
"""

import logging
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import Depends

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.models.attachment import AttachmentIn
from object_storage_api.repositories.attachment import AttachmentRepo
from object_storage_api.schemas.attachment import AttachmentPostResponseSchema, AttachmentPostSchema
from object_storage_api.stores.attachment import AttachmentStore

logger = logging.getLogger()


class AttachmentService:
    """
    Service for managing attachments.
    """

    def __init__(
        self,
        attachment_repository: Annotated[AttachmentRepo, Depends(AttachmentRepo)],
        attachment_store: Annotated[AttachmentStore, Depends(AttachmentStore)],
    ) -> None:
        """
        Initialise the `AttachmentService` with an `AttachmentRepo` repository.

        :param attachment_repository: `AttachmentRepo` repository to use.
        :param attachment_store: `AttachmentStore` store to use.
        """
        self._attachment_repository = attachment_repository
        self._attachment_store = attachment_store

    def create(self, attachment: AttachmentPostSchema) -> AttachmentPostResponseSchema:
        """
        Create a new attachment.

        :param attachment: Attachment to be created.
        :return: Created attachment with an pre-signed upload URL.
        :raises InvalidObjectIdError: If the attachment has any invalid ID's in it.
        """

        # Generate a unique ID for the attachment - this needs to be known now to avoid inserting into the database
        # before generating the presigned URL which would then require transactions
        attachment_id = str(ObjectId())

        object_key, upload_info = self._attachment_store.create_presigned_post(attachment_id, attachment)

        try:
            attachment_in = AttachmentIn(**attachment.model_dump(), id=attachment_id, object_key=object_key)
        except InvalidObjectIdError as exc:
            # Provide more specific detail
            exc.response_detail = "Invalid `entity_id` given"
            raise exc

        attachment_out = self._attachment_repository.create(attachment_in)

        return AttachmentPostResponseSchema(**attachment_out.model_dump(), upload_info=upload_info)

    def list(self, entity_id: Optional[str] = None) -> list[AttachmentPostResponseSchema]:
        """
        Retrieve a list of attachments based on the provided filters.

        :param entity_id: The ID of the entity to filter attachments by.
        :return: List of attachments or an empty list if no attachments are retrieved.
        """

        attachments = self._attachment_repository.list(entity_id)

        attachments_list = []

        for attachment in attachments:
            object_key, upload_info = self._attachment_store.create_presigned_post(attachment.id, attachment)
            attachments_list.append(AttachmentPostResponseSchema(**attachment.model_dump(), upload_info=upload_info))

        return attachments_list
