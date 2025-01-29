"""
Module for providing an API router which defines routes for managing attachments using the `AttachmentService`
service.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.schemas.attachment import (
    AttachmentMetadataSchema,
    AttachmentPostResponseSchema,
    AttachmentPostSchema,
    AttachmentSchema,
)
from object_storage_api.services.attachment import AttachmentService

logger = logging.getLogger()


router = APIRouter(prefix="/attachments", tags=["attachments"])

AttachmentServiceDep = Annotated[AttachmentService, Depends(AttachmentService)]


@router.post(
    path="",
    summary="Create a new attachment",
    response_description="Information about the created attachment including a presigned URL to upload the file to",
    status_code=status.HTTP_201_CREATED,
)
def create_attachment(
    attachment: AttachmentPostSchema, attachment_service: AttachmentServiceDep
) -> AttachmentPostResponseSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Creating a new attachment")
    logger.debug("Attachment data: %s", attachment)

    return attachment_service.create(attachment)


@router.get(
    path="",
    summary="Get attachments",
    response_description="List of attachments",
)
def get_attachments(
    attachment_service: AttachmentServiceDep,
    entity_id: Annotated[Optional[str], Query(description="Filter attachments by entity ID")] = None,
) -> list[AttachmentMetadataSchema]:
    # pylint: disable=missing-function-docstring
    logger.info("Getting attachments")

    if entity_id is not None:
        logger.debug("Entity ID filter: '%s'", entity_id)

    return attachment_service.list(entity_id)


@router.get(path="/{attachment_id}", summary="Get an attachment by ID", response_description="Single attachment")
def get_attachment(
    attachment_id: Annotated[str, Path(description="ID of the attachment to get")],
    attachment_service: AttachmentServiceDep,
) -> AttachmentSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Getting attachment with ID: %s", attachment_id)

    return attachment_service.get(attachment_id)


@router.delete(
    path="/{attachment_id}",
    summary="Delete an attachment by ID",
    response_description="Attachment deleted successfully",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachment(
    attachment_id: Annotated[str, Path(description="The ID of the attachment to delete")],
    attachment_service: AttachmentServiceDep,
) -> None:
    # pylint: disable=missing-function-docstring
    logger.info("Deleting attachment with ID: %s", attachment_id)
    attachment_service.delete(attachment_id)


@router.delete(
    path="",
    summary="Delete attachments by entity ID",
    response_description="Attachments deleted successfully",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachments_by_entity_id(
    entity_id: Annotated[str, Query(description="The entity ID of the attachments to delete")],
    attachment_service: AttachmentServiceDep,
) -> None:
    # pylint: disable=missing-function-docstring
    logger.info("Deleting attachments with entity ID: %s", entity_id)
    try:
        attachment_service.delete_by_entity_id(entity_id)
    except InvalidObjectIdError:
        # As this endpoint takes in a query parameter to delete multiple attachments, and to hide the database
        # behaviour, we treat any invalid entity_id the same as a valid one that has no attachments associated to it.
        pass
