"""
Module for providing an API router which defines routes for managing attachments using the `AttachmentService`
service.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from object_storage_api.core.exceptions import InvalidObjectIdError
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

    try:
        return attachment_service.create(attachment)
    except InvalidObjectIdError as exc:
        message = "Invalid entity_id"
        logger.exception(message)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message) from exc
