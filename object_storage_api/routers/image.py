"""
Module for providing an API router which defines routes for managing images using the `ImageService`
service.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

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
def create_image(image: ImagePostSchema, image_service: ImageServiceDep) -> ImageSchema:
    # pylint: disable=missing-function-docstring
    logger.info("Creating a new image")
    logger.debug("Image data: %s", image)

    return image_service.create(image)
