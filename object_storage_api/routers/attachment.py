"""
Module for providing an API router which defines routes for managing attachments using the `AttachmentService`
service.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from object_storage_api.schemas.attachment import AttachmentPostResponseSchema, AttachmentPostSchema
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
) -> list[AttachmentPostResponseSchema]:
    # pylint: disable=missing-function-docstring
    logger.info("Getting attachments")

    if entity_id is not None:
        logger.debug("Entity ID filter: '%s'", entity_id)

    return attachment_service.list(entity_id)
