"""
Module for providing a service for managing images using the `ImageRepo` repository and `ImageStore`
store.
"""

import logging
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import Depends, UploadFile

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.core.image import generate_thumbnail_base64_str
from object_storage_api.models.image import ImageIn
from object_storage_api.repositories.image import ImageRepo
from object_storage_api.schemas.image import ImageMetadataSchema, ImagePostMetadataSchema, ImageSchema
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

    def create(self, image_metadata: ImagePostMetadataSchema, upload_file: UploadFile) -> ImageMetadataSchema:
        """
        Create a new image.

        :param image_metadata: Metadata of the image to be created.
        :param upload_file: Upload file of the image to be created.
        :return: Created image with an pre-signed upload URL.
        :raises InvalidObjectIdError: If the image has any invalid ID's in it.
        """

        # Generate a unique ID for the image - this needs to be known now to avoid inserting into the database
        # before generating the presigned URL which would then require transactions
        image_id = str(ObjectId())

        # Generate the thumbnail
        thumbnail_base64 = generate_thumbnail_base64_str(upload_file)

        # Upload the full size image to object storage
        object_key = self._image_store.upload(image_id, image_metadata, upload_file)

        try:
            image_in = ImageIn(
                **image_metadata.model_dump(),
                id=image_id,
                file_name=upload_file.filename,
                object_key=object_key,
                thumbnail_base64=thumbnail_base64,
            )
        except InvalidObjectIdError as exc:
            # Provide more specific detail
            exc.response_detail = "Invalid `entity_id` given"
            raise exc

        image_out = self._image_repository.create(image_in)

        return ImageMetadataSchema(**image_out.model_dump())

    def get(self, image_id: str) -> ImageSchema:
        """
        Retrieve an image's metadata with its presigned get url by its ID.

        :param image_id: ID of the image to retrieve.
        :return: An image's metadata with a presigned get url.
        """
        image = self._image_repository.get(image_id=image_id)
        presigned_url = self._image_store.create_presigned_get(image)
        return ImageSchema(**image.model_dump(), url=presigned_url)

    def list(self, entity_id: Optional[str] = None, primary: Optional[bool] = None) -> list[ImageMetadataSchema]:
        """
        Retrieve a list of images based on the provided filters.

        :param entity_id: The ID of the entity to filter images by.
        :param primary: The primary value to filter images by.
        :return: List of images or an empty list if no images are retrieved.
        """
        images = self._image_repository.list(entity_id, primary)
        return [ImageMetadataSchema(**image.model_dump()) for image in images]

    def delete(self, image_id: str) -> None:
        """
        Delete an image by its ID.

        :param image_id: The ID of the image to delete.
        """
        stored_image = self._image_repository.get(image_id)
        # Deletes image from object store first to prevent unreferenced objects in storage
        self._image_store.delete(stored_image.object_key)
        self._image_repository.delete(image_id)
