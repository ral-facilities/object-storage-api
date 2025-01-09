"""
Module for providing an API router which defines routes for managing attachments using the `AttachmentService`
service.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status

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


@router.get(
    path="/{attachment_id}",
    summary="Get an attachment by ID",
    response_description="Single attachment",
)
def get_attachment(
    attachment_id: Annotated[str, Path(description="ID of the attachment to get")],
    attachment_service: AttachmentServiceDep,
) -> AttachmentSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Getting attachment with ID: %s", attachment_id)

    return attachment_service.get(attachment_id)
