"""
Module for providing a repository for managing images in a MongoDB database.
"""

import logging
from typing import Optional

from pymongo import UpdateMany, UpdateOne
from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from object_storage_api.core.config import config
from object_storage_api.core.custom_object_id import CustomObjectId
from object_storage_api.core.database import DatabaseDep
from object_storage_api.core.exceptions import (
    DuplicateRecordError,
    InvalidObjectIdError,
    MissingRecordError,
    UploadLimitReachedError,
)
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

    def create(self, image: ImageIn, session: Optional[ClientSession] = None) -> ImageOut:
        """
        Create a new image in a MongoDB database.

        :param image: Image to be created.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Created image.
        :raises UploadLimitReachedError: If the upload limit has been reached.
        :raises DuplicateRecordError: If a duplicate image is found within the parent entity.
        """

        if self._count_by_entity_id(image.entity_id, session=session) >= config.image.upload_limit:
            raise UploadLimitReachedError(
                detail="Unable to create an image as the upload limit for images "
                f"with `entity_id` '{image.entity_id}' has been reached",
                entity_name="image",
            )

        if self._is_duplicate(image.entity_id, image.code, session=session):
            raise DuplicateRecordError("Duplicate image found within the parent entity", entity_name="image")

        logger.info("Inserting the new image into the database")
        result = self._images_collection.insert_one(image.model_dump(by_alias=True), session=session)
        return self.get(str(result.inserted_id), session=session)

    def get(self, image_id: str, session: Optional[ClientSession] = None) -> ImageOut:
        """
        Retrieve an image by its ID from a MongoDB database.

        :param image_id: ID of the image to retrieve.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Retrieved image if found.
        :raises MissingRecordError: If the supplied `image_id` is non-existent.
        :raises InvalidObjectIdError: If the supplied `image_id` is invalid.
        """
        logger.info("Retrieving image with ID: %s from the database", image_id)
        try:
            image_id = CustomObjectId(image_id)
            image = self._images_collection.find_one({"_id": image_id}, session=session)
        except InvalidObjectIdError as exc:
            exc.status_code = 404
            exc.response_detail = "Image not found"
            raise exc
        if image:
            return ImageOut(**image)
        raise MissingRecordError(detail=f"No image found with ID: {image_id}", entity_name="image")

    def list(
        self, entity_id: Optional[str], primary: Optional[bool], session: Optional[ClientSession] = None
    ) -> list[ImageOut]:
        """
        Retrieve images from a MongoDB database.

        :param session: PyMongo ClientSession to use for database operations.
        :param entity_id: The ID of the entity to filter images by.
        :param primary: The primary value to filter images by.
        :return: List of images or an empty list if no images are retrieved.
        """

        # There is some duplicate code here, due to the attachments and images methods being very similar
        # pylint: disable=duplicate-code

        query = {}

        if entity_id is not None:
            try:
                query["entity_id"] = CustomObjectId(entity_id)
            except InvalidObjectIdError:
                # As this method filters, and to hide the database behaviour, we treat any invalid id
                # the same as a valid one that doesn't exist i.e. return an empty list
                return []

        if primary is not None:
            query["primary"] = primary

        message = "Retrieving all images from the database"
        if not query:
            logger.info(message)
        else:
            logger.info("%s matching the provided filter(s)", message)
            logger.debug("Provided filter(s): %s", query)

        # pylint: enable=duplicate-code

        images = self._images_collection.find(query, session=session)
        return [ImageOut(**image) for image in images]

    def update(self, image_id: str, image: ImageIn, update_primary: bool, session: ClientSession = None) -> ImageOut:
        """
        Updates an image by its ID in a MongoDB database.

        :param image_id: The ID of the image to update.
        :param image: The image containing the update data.
        :param update_primary: Decides whether to set primary to False for other images.
        :param session: PyMongo ClientSession to use for database operations.
        :return: The updated image.
        :raises InvalidObjectIdError: If the supplied `image_id` is invalid.
        :raises DuplicateRecordError: If a duplicate attachment is found within the parent entity.
        """

        try:
            image_id = CustomObjectId(image_id)
        except InvalidObjectIdError as exc:
            exc.status_code = 404
            exc.response_detail = "Image not found"
            raise exc

        stored_image = self.get(str(image_id), session=session)
        if image.file_name != stored_image.file_name and self._is_duplicate(
            image.entity_id, image.code, image_id, session=session
        ):
            raise DuplicateRecordError("Duplicate image found within the parent entity", entity_name="image")

        logger.info("Updating image metadata with ID: %s", image_id)
        if update_primary:
            bulkwrite_update = [
                UpdateMany(filter={"primary": True, "entity_id": image.entity_id}, update={"$set": {"primary": False}}),
                UpdateOne(filter={"_id": image_id}, update={"$set": image.model_dump(by_alias=True)}),
            ]
            self._images_collection.bulk_write(bulkwrite_update, session=session)
        else:
            self._images_collection.update_one(
                {"_id": image_id}, {"$set": image.model_dump(by_alias=True)}, session=session
            )

        return self.get(image_id=str(image_id), session=session)

    def delete(self, image_id: str, session: Optional[ClientSession] = None) -> None:
        """
        Delete an image by its ID from a MongoDB database.

        :param image_id: The ID of the image to delete.
        :param session: PyMongo ClientSession to use for database operations
        :raises MissingRecordError: If the supplied `image_id` is non-existent.
        :raises InvalidObjectIdError: If the supplied `image_id` is invalid.
        """
        logger.info("Deleting image with ID: %s from the database", image_id)
        try:
            image_id = CustomObjectId(image_id)
        except InvalidObjectIdError as exc:
            exc.status_code = 404
            exc.response_detail = "Image not found"
            raise exc
        response = self._images_collection.delete_one(filter={"_id": image_id}, session=session)
        if response.deleted_count == 0:
            raise MissingRecordError(f"No image found with ID: {image_id}", entity_name="image")

    def delete_by_entity_id(self, entity_id: str, session: Optional[ClientSession] = None) -> None:
        """
        Delete images by entity ID.

        :param entity_id: The entity ID of the images to delete.
        :param session: PyMongo ClientSession to use for database operations.
        """
        logger.info("Deleting images with entity ID: %s from the database", entity_id)
        try:
            entity_id = CustomObjectId(entity_id)
            # Given it is deleting multiple, we are not raising an exception if no images were found to be deleted
            self._images_collection.delete_many(filter={"entity_id": entity_id}, session=session)
        except InvalidObjectIdError:
            # As this method takes in an entity_id to delete multiple images, and to hide the database behaviour, we
            # treat any invalid entity_id the same as a valid one that has no images associated to it.
            pass

    def _count_by_entity_id(self, entity_id: CustomObjectId, session: Optional[ClientSession] = None) -> int:
        """
        Count the number of images matching the provided entity ID in a MongoDB database.

        :param entity_id: The entity ID to use to select which documents to count.
        :param session: PyMongo ClientSession to use for database operations.
        """
        logger.info("Counting number of images with entity ID: %s in the database", entity_id)
        return self._images_collection.count_documents(filter={"entity_id": entity_id}, session=session)

    def _is_duplicate(
        self,
        entity_id: CustomObjectId,
        code: str,
        image_id: Optional[CustomObjectId] = None,
        session: Optional[ClientSession] = None,
    ) -> bool:
        """
        Check if an image with the same code already exists for the same entity.

        :param entity_id: ID of the entity.
        :param code: Code of the image to check for duplicates.
        :param image_id: ID of the image to check if the duplicate image found is itself.
        :param session: PyMongo ClientSession to use for database operations
        :return: `True` if a duplicate image code is found, `False` otherwise.
        """
        logger.info("Checking if image with code '%s' already exists within the entity with id '%s'", code, entity_id)

        return (
            self._images_collection.find_one(
                {"entity_id": entity_id, "code": code, "_id": {"$ne": image_id}},
                session=session,
            )
            is not None
        )
