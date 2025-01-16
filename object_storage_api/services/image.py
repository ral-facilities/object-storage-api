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
from object_storage_api.schemas.image import (
    ImageMetadataSchema,
    ImagePatchMetadataSchema,
    ImagePostMetadataSchema,
    ImageSchema,
)
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
        Retrieve an image's metadata with its presigned get download and inline urls by its ID.

        :param image_id: ID of the image to retrieve.
        :return: An image's metadata with its presigned get urls.
        """
        image = self._image_repository.get(image_id=image_id)
        (inline_url, download_url) = self._image_store.create_presigned_get(image)
        return ImageSchema(**image.model_dump(), inline_url=inline_url, download_url=download_url)

    def list(self, entity_id: Optional[str] = None, primary: Optional[bool] = None) -> list[ImageMetadataSchema]:
        """
        Retrieve a list of images based on the provided filters.

        :param entity_id: The ID of the entity to filter images by.
        :param primary: The primary value to filter images by.
        :return: List of images or an empty list if no images are retrieved.
        """
        images = self._image_repository.list(entity_id, primary)
        return [ImageMetadataSchema(**image.model_dump()) for image in images]

    def update(self, image_id: str, image: ImagePatchMetadataSchema) -> ImageMetadataSchema:
        """
        Update an image by its ID.

        :param image_id: The ID of the image to update.
        :param image: The image containing the fields to be updated.
        :return: The updated image.
        """
        stored_image = self._image_repository.get(image_id=image_id)
        update_data = image.model_dump(exclude_unset=True)

        update_primary = image.primary is not None and image.primary is True and stored_image.primary is False
        updated_image = self._image_repository.update(
            image_id=image_id,
            image=ImageIn(**{**stored_image.model_dump(), **update_data}),
            update_primary=update_primary,
        )

        return ImageMetadataSchema(**updated_image.model_dump())

    def delete(self, image_id: str) -> None:
        """
        Delete an image by its ID.

        :param image_id: The ID of the image to delete.
        """
        stored_image = self._image_repository.get(image_id)
        # Deletes image from object store first to prevent unreferenced objects in storage
        self._image_store.delete(stored_image.object_key)
        self._image_repository.delete(image_id)
