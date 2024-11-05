"""
Module for providing an API router which defines routes for managing images using the `ImageService`
service.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from object_storage_api.schemas.image import ImagePostMetadataSchema, ImageSchema
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
# pylint:disable=too-many-positional-arguments
def create_image(
    image_service: ImageServiceDep,
    # Unfortunately using Annotated[ImagePostSchema, Form()] as on
    # https://fastapi.tiangolo.com/tutorial/request-form-models/ does not work correctly when there is an UploadFile
    # within it, so have to redefine here before passing them to the schema
    entity_id: Annotated[str, Form(description="ID of the entity the image relates to")],
    upload_file: Annotated[UploadFile, File(description="Image file")],
    title: Annotated[Optional[str], Form(description="Title of the image")] = None,
    description: Annotated[Optional[str], Form(description="Description of the image")] = None,
) -> ImageSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Creating a new image")

    image_metadata = ImagePostMetadataSchema(entity_id=entity_id, title=title, description=description)

    logger.debug("Image metadata: %s", image_metadata)
    logger.debug("Image upload file: %s", upload_file)

    return image_service.create(image_metadata, upload_file)


@router.get(
    path="",
    summary="Get images",
    response_description="List of images",
)
def get_images(
    image_service: ImageServiceDep,
    entity_id: Annotated[Optional[str], Query(description="Filter images by entity ID")] = None,
    primary: Annotated[Optional[bool], Query(description="Filter images by primary")] = None,
) -> list[ImageSchema]:
    # pylint: disable=missing-function-docstring
    logger.info("Getting images")

    if entity_id:
        logger.debug("Entity ID filter: '%s'", entity_id)

    if primary:
        logger.debug("Primary filter: '%s'", primary)

    return image_service.list(entity_id, primary)
