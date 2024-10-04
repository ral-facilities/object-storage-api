"""
Module for providing a service for managing images using the `ImageRepo` repository and `ImageStore`
store.
"""

import logging
from typing import Annotated

from bson import ObjectId
from fastapi import Depends

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.models.image import ImageIn
from object_storage_api.repositories.image import ImageRepo
from object_storage_api.schemas.image import ImagePostSchema, ImageSchema
from object_storage_api.stores.image import ImageStore

logger = logging.getLogger()


class ImageService:
    """
    Service for managing images.
    """

    def __init__(
        self,
        image_repository: Annotated[ImageRepo, Depends(ImageRepo)],
        image_store: Annotated[ImageStore, Depends(ImageStore)],
    ) -> None:
        """
        Initialise the `ImageService` with an `ImageRepo` repository.

        :param image_repository: `ImageRepo` repository to use.
        :param image_store: `ImageStore` store to use.
        """
        self._image_repository = image_repository
        self._image_store = image_store

    def create(self, image: ImagePostSchema) -> ImageSchema:
        """
        Create a new image.

        :param image: Image to be created.
        :return: Created image with an pre-signed upload URL.
        :raises InvalidObjectIdError: If the image has any invalid ID's in it.
        """

        # Generate a unique ID for the image - this needs to be known now to avoid inserting into the database
        # before generating the presigned URL which would then require transactions
        image_id = str(ObjectId())

        object_key = self._image_store.upload_image(image_id, image)

        try:
            image_in = ImageIn(**image.model_dump(), id=image_id, object_key=object_key)
        except InvalidObjectIdError as exc:
            # Provide more specific detail
            exc.response_detail = "Invalid `entity_id` given"
            raise exc

        image_out = self._image_repository.create(image_in)

        return ImageSchema(**image_out.model_dump())
