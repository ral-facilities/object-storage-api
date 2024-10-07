"""
Module for providing a service for managing images using the `ImageRepo` repository and `ImageStore`
store.
"""

import base64
import logging
from io import BytesIO
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, UploadFile
from PIL import Image

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.models.image import ImageIn
from object_storage_api.repositories.image import ImageRepo
from object_storage_api.schemas.image import ImagePostMetadataSchema, ImageSchema
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

    # TODO: Move elsewhere so not in service?
    def _generate_thumbnail(self, upload_file: UploadFile) -> str:
        """
        Generates a thumbnail from an uploaded image file.

        :param upload_file: Uploaded image file.
        :return: Base64 encoded string of the thumbnail
        """
        pillow_image = Image.open(upload_file.file)
        # TODO: Make configurable
        thumbnail_size = (300, 300)
        # TODO: Which resampling to use
        # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters-comparison-table?
        pillow_image.thumbnail(thumbnail_size)

        # Save into memory buffer using the WebP image format (There are other options available at
        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp)
        memory_image_buffer = BytesIO()
        pillow_image.save(memory_image_buffer, "webp")

        # Move buffer back to start ready for reading (it will be a the end after saving)
        upload_file.seek(0)

        # Encode the thumbnail into a bytestring
        thumbnail_bytestring = base64.b64encode(memory_image_buffer.getvalue()).decode("utf-8")

        return thumbnail_bytestring

    def create(self, image_metadata: ImagePostMetadataSchema, upload_file: UploadFile) -> ImageSchema:
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
        thumbnail = self._generate_thumbnail(upload_file)

        # Upload the full size image to object storage
        object_key = self._image_store.upload(image_id, image_metadata, upload_file)

        try:
            image_in = ImageIn(
                **image_metadata.model_dump(),
                id=image_id,
                file_name=upload_file.filename,
                object_key=object_key,
                thumbnail=thumbnail,
            )
        except InvalidObjectIdError as exc:
            # Provide more specific detail
            exc.response_detail = "Invalid `entity_id` given"
            raise exc

        image_out = self._image_repository.create(image_in)

        return ImageSchema(**image_out.model_dump())
