"""
Module for providing an API router which defines routes for managing images using the `ImageService`
service.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from object_storage_api.schemas.image import ImagePostSchema, ImageSchema
from object_storage_api.services.image import ImageService

logger = logging.getLogger()


router = APIRouter(prefix="/images", tags=["images"])

ImageServiceDep = Annotated[ImageService, Depends(ImageService)]


@router.post(
    path="",
    summary="Create a new image",
    response_description="Information about the created image",
    status_code=status.HTTP_201_CREATED,
)
# pylint:disable=too-many-arguments
def create_image(
    image_service: ImageServiceDep,
    # Unfortunately using Annotated[ImagePostSchema, Form()] as on
    # https://fastapi.tiangolo.com/tutorial/request-form-models/does not work correctly when there is an UploadFile
    # within it, so have to redefine here before passing them to the schema
    entity_id: Annotated[str, Form(description="ID of the entity the image relates to")],
    file_name: Annotated[str, Form(description="File name of the image")],
    file: Annotated[UploadFile, File(description="Image file")],
    title: Annotated[Optional[str], Form(description="Title of the image")] = None,
    description: Annotated[Optional[str], Form(description="Description of the image")] = None,
) -> ImageSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Creating a new image")

    image = ImagePostSchema(entity_id=entity_id, file_name=file_name, file=file, title=title, description=description)

    logger.debug("Image data: %s", image)

    return image_service.create(image)
