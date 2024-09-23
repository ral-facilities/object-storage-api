"""
Module for providing a service for managing attachments using the `AttachmentRepo` repository and `AttachmentStore`
store.
"""

import logging
from typing import Annotated

from fastapi import Depends

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

    # TODO: In inventory_management_system we return the output model here, should it have been schema?
    def create(self, attachment: AttachmentPostSchema) -> AttachmentPostResponseSchema:
        """
        Create a new attachment.

        :param attachment: Attachment to be created.
        :return: Created attachment with an pre-signed upload URL.
        """

        # TODO: Use a database transaction here? Depends whether URL generated first or second
        # and what happens with duplicates
        attachment_in, upload_url = self._attachment_store.generate_presigned_upload_url(attachment)
        attachment_out = self._attachment_repository.create(attachment_in)

        return AttachmentPostResponseSchema(**attachment_out.model_dump(), upload_url=upload_url)
