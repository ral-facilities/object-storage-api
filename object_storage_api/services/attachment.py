"""
Module for providing a service for managing attachments using the `AttachmentRepo` repository and `AttachmentStore`
store.
"""

import logging
from typing import Annotated

from bson import ObjectId
from fastapi import Depends

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

    # TODO: In inventory_management_system we return the output model here, should it have been schema?
    def create(self, attachment: AttachmentPostSchema) -> AttachmentPostResponseSchema:
        """
        Create a new attachment.

        :param attachment: Attachment to be created.
        :return: Created attachment with an pre-signed upload URL.
        """

        return AttachmentPostResponseSchema(
            **attachment.model_dump(), id=str(ObjectId()), upload_url="http://www.example.com"
        )
