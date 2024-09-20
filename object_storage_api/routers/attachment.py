# TODO: Update if name for AttachmentService is different
"""
Module for providing an API router which defines routes for managing attachments using the `AttachmentService`
service.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from object_storage_api.schemas.attachment import AttachmentPostResponseSchema, AttachmentPostSchema
from object_storage_api.services.attachment import AttachmentService

logger = logging.getLogger()


router = APIRouter(prefix="/attachments", tags=["attachments"])

AttachmentServiceDep = Annotated[AttachmentService, Depends(AttachmentService)]


# TODO: Fill out description when have a model, also need to add return type on function below
@router.post(path="", summary="Create a new attachment", response_description="", status_code=status.HTTP_201_CREATED)
def create_attachment(
    attachment: AttachmentPostSchema, attachment_service: AttachmentServiceDep
) -> AttachmentPostResponseSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Creating a new attachment")
    logger.debug("Attachment data: %s", attachment)

    # TODO: Error handling
    return attachment_service.create(attachment)
