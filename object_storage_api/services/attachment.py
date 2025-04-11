"""
Module for providing a service for managing attachments using the `AttachmentRepo` repository and `AttachmentStore`
store.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import Depends

from object_storage_api.core.config import config
from object_storage_api.core.custom_object_id import CustomObjectId
from object_storage_api.core.exceptions import (
    FileTypeMismatchException,
    InvalidObjectIdError,
    UnsupportedFileExtensionException,
    UploadLimitReachedError,
)
from object_storage_api.models.attachment import AttachmentIn
from object_storage_api.repositories.attachment import AttachmentRepo
from object_storage_api.schemas.attachment import (
    AttachmentMetadataSchema,
    AttachmentPatchMetadataSchema,
    AttachmentPostResponseSchema,
    AttachmentPostSchema,
    AttachmentSchema,
)
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
        :return: Created attachment with a pre-signed upload URL.
        :raises InvalidObjectIdError: If the attachment has any invalid ID's in it.
        :raises UploadLimitReachedError: If the upload limit has been reached.
        :raises UnsupportedFileExtensionException: If the file extension of the attachment is not supported.
        """
        try:
            CustomObjectId(attachment.entity_id)
        except InvalidObjectIdError as exc:
            # Provide more specific detail
            exc.response_detail = "Invalid `entity_id` given"
            raise exc

        if self._attachment_repository.count_by_entity_id(attachment.entity_id) >= config.attachment.upload_limit:
            raise UploadLimitReachedError(
                detail="Unable to create an attachment as the upload limit for attachments "
                f"with `entity_id` '{attachment.entity_id}' has been reached",
                entity_name="attachment",
            )

        file_extension = Path(attachment.file_name).suffix
        if not file_extension or file_extension.lower() not in config.attachment.allowed_file_extensions:
            raise UnsupportedFileExtensionException(f"File extension of '{attachment.file_name}' is not supported")

        # Generate a unique ID for the attachment - this needs to be known now to avoid inserting into the database
        # before generating the presigned URL which would then require transactions
        attachment_id = str(ObjectId())

        object_key, upload_info = self._attachment_store.create_presigned_post(attachment_id, attachment)

        attachment_in = AttachmentIn(**attachment.model_dump(), id=attachment_id, object_key=object_key)
        attachment_out = self._attachment_repository.create(attachment_in)

        return AttachmentPostResponseSchema(**attachment_out.model_dump(), upload_info=upload_info)

    def get(self, attachment_id: str) -> AttachmentSchema:
        """
        Retrieve an attachment's metadata with its presigned get download url by its ID.

        :param attachment_id: ID of the attachment to retrieve.
        :return: An attachment's metadata with a presigned get download url.
        """

        attachment = self._attachment_repository.get(attachment_id=attachment_id)
        download_url = self._attachment_store.create_presigned_get(attachment)
        return AttachmentSchema(**attachment.model_dump(), download_url=download_url)

    def list(self, entity_id: Optional[str] = None) -> list[AttachmentMetadataSchema]:
        """
        Retrieve a list of attachments based on the provided filters.

        :param entity_id: The ID of the entity to filter attachments by.
        :return: List of attachments or an empty list if no attachments are retrieved.
        """

        attachments = self._attachment_repository.list(entity_id)

        return [AttachmentMetadataSchema(**attachment.model_dump()) for attachment in attachments]

    def update(self, attachment_id: str, attachment: AttachmentPatchMetadataSchema) -> AttachmentMetadataSchema:
        """
        Update an attachment by its ID.

        :param attachment_id: The ID of the attachment to update.
        :param attachment: The attachment containing the fields to be updated.
        :return: The updated attachment.
        :raises FileTypeMismatchException: If the extensions of the stored and updated attachment do not match.
        """

        stored_attachment = self._attachment_repository.get(attachment_id=attachment_id)

        if attachment.file_name is not None:
            stored_type, _ = mimetypes.guess_type(stored_attachment.file_name)
            update_type, _ = mimetypes.guess_type(attachment.file_name)
            if update_type != stored_type:
                raise FileTypeMismatchException(
                    f"Patch filename extension of '{attachment.file_name}' does not match "
                    f"that of the stored attachment '{stored_attachment.file_name}'"
                )

        updated_attachment = self._attachment_repository.update(
            attachment_id=attachment_id,
            attachment=AttachmentIn(**{**stored_attachment.model_dump(), **attachment.model_dump(exclude_unset=True)}),
        )

        return AttachmentMetadataSchema(**updated_attachment.model_dump())

    def delete(self, attachment_id: str) -> None:
        """
        Delete an attachment by its ID.
        :param attachment_id: The ID of the attachment to delete.
        """
        stored_attachment = self._attachment_repository.get(attachment_id)
        # Deletes attachment from object store first to prevent unreferenced objects in storage
        self._attachment_store.delete(stored_attachment.object_key)
        self._attachment_repository.delete(attachment_id)

    def delete_by_entity_id(self, entity_id: str) -> None:
        """
        Delete attachments by entity ID.

        :param entity_id: The entity ID of the attachments to delete.
        """
        stored_attachments = self._attachment_repository.list(entity_id)
        if stored_attachments:
            # Deletes attachments from object store first to prevent unreferenced objects in storage
            self._attachment_store.delete_many(
                [stored_attachment.object_key for stored_attachment in stored_attachments]
            )
            self._attachment_repository.delete_by_entity_id(entity_id)
