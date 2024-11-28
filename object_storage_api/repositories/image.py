"""
Module for providing a repository for managing images in a MongoDB database.
"""

import logging
from typing import Optional

from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from object_storage_api.core.custom_object_id import CustomObjectId
from object_storage_api.core.database import DatabaseDep
from object_storage_api.core.exceptions import InvalidObjectIdError, MissingRecordError
from object_storage_api.models.image import ImageIn, ImageOut

logger = logging.getLogger()


class ImageRepo:
    """
    Repository for managing images in a MongoDB database.
    """

    def __init__(self, database: DatabaseDep) -> None:
        """
        Initialise the `ImageRepo` with a MongoDB database instance.

        :param database: Database to use.
        """
        self._database = database
        self._images_collection: Collection = self._database.images

    def create(self, image: ImageIn, session: ClientSession = None) -> ImageOut:
        """
        Create a new image in a MongoDB database.

        :param image: Image to be created.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Created image.
        """

        logger.info("Inserting the new image into the database")
        result = self._images_collection.insert_one(image.model_dump(by_alias=True), session=session)
        return self.get(str(result.inserted_id), session=session)

    def get(self, image_id: str, session: ClientSession = None) -> Optional[ImageOut]:
        """
        Retrieve an image by its ID from a MongoDB database.

        :param image_id: ID of the image to retrieve.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Retrieved image or `None` if not found.
        :raises MissingRecordError: If the supplied `image_id` is invalid or non-existent.
        """
        logger.info("Retrieving image with ID: %s from the database", image_id)
        message = f"Image with image_id {image_id} was not found."
        entity_name = "image"
        try:
            image_id = CustomObjectId(image_id)
            image = self._images_collection.find_one({"_id": image_id}, session=session)
        except InvalidObjectIdError as exc:
            raise MissingRecordError(detail=message, entity_name=entity_name) from exc
        if image:
            return ImageOut(**image)
        raise MissingRecordError(detail=message, entity_name=entity_name)

    def list(self, entity_id: Optional[str], primary: Optional[bool], session: ClientSession = None) -> list[ImageOut]:
        """
        Retrieve images from a MongoDB database.

        :param session: PyMongo ClientSession to use for database operations.
        :param entity_id: The ID of the entity to filter images by.
        :param primary: The primary value to filter images by.
        :return: List of images or an empty list if no images are retrieved.
        """

        query = {}
        if entity_id is not None:
            query["entity_id"] = CustomObjectId(entity_id)
        if primary is not None:
            query["primary"] = primary

        message = "Retrieving all images from the database"
        if not query:
            logger.info(message)
        else:
            logger.info("%s matching the provided filter(s)", message)
            logger.debug("Provided filter(s): %s", query)

        images = self._images_collection.find(query, session=session)
        return [ImageOut(**image) for image in images]
