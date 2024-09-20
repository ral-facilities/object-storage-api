# TODO: Update if name for AttachmentService is different
"""
Module for providing an API router which defines routes for managing attachments using the `AttachmentService`
service.
"""

import logging

from bson import ObjectId
from fastapi import APIRouter, status

from object_storage_api.schemas.attachment import AttachmentPostResponseSchema, AttachmentPostSchema

logger = logging.getLogger()


router = APIRouter(prefix="/attachments", tags=["attachments"])


# TODO: Fill out description when have a model, also need to add return type on function below
@router.post(path="", summary="Create a new attachment", response_description="", status_code=status.HTTP_201_CREATED)
def create_attachment(attachment: AttachmentPostSchema) -> AttachmentPostResponseSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Creating a new attachment")
    logger.debug("Attachment data: %s", attachment)

    # TODO: Implement
    return AttachmentPostResponseSchema(
        **attachment.model_dump(), id=str(ObjectId()), upload_url="http://www.example.com"
    )
