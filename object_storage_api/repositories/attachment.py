"""
Module for providing a repository for managing attachments in a MongoDB database.
"""

import logging
from typing import Optional

from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from object_storage_api.core.custom_object_id import CustomObjectId
from object_storage_api.core.database import DatabaseDep
from object_storage_api.core.exceptions import DuplicateRecordError, InvalidObjectIdError, MissingRecordError
from object_storage_api.models.attachment import AttachmentIn, AttachmentOut

logger = logging.getLogger()


class AttachmentRepo:
    """
    Repository for managing attachments in a MongoDB database.
    """

    def __init__(self, database: DatabaseDep) -> None:
        """
        Initialise the `AttachmentRepo` with a MongoDB database instance.

        :param database: Database to use.
        """
        self._database = database
        self._attachments_collection: Collection = self._database.attachments

    def create(self, attachment: AttachmentIn, session: Optional[ClientSession] = None) -> AttachmentOut:
        """
        Create a new attachment in a MongoDB database.

        :param attachment: Attachment to be created.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Created attachment.
        """

        if self._is_duplicate(attachment.entity_id, attachment.code, session=session):
            raise DuplicateRecordError("Duplicate attachment found within the parent entity", entity_name="attachment")

        logger.info("Inserting the new attachment into the database")
        result = self._attachments_collection.insert_one(attachment.model_dump(by_alias=True), session=session)
        return self.get(str(result.inserted_id), session=session)

    def get(self, attachment_id: str, session: Optional[ClientSession] = None) -> Optional[AttachmentOut]:
        """
        Retrieve an attachment by its ID from a MongoDB database.

        :param attachment_id: ID of the attachment to retrieve.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Retrieved attachment if found.
        :raises MissingRecordError: If the supplied `attachment_id` is non-existent.
        :raises InvalidObjectIdError: If the supplied `attachment_id` is invalid.
        """

        logger.info("Retrieving attachment with ID: %s from the database", attachment_id)

        try:
            attachment_id = CustomObjectId(attachment_id)
            attachment = self._attachments_collection.find_one({"_id": attachment_id}, session=session)
        except InvalidObjectIdError as exc:
            exc.status_code = 404
            exc.response_detail = "Attachment not found"
            raise exc

        if attachment:
            return AttachmentOut(**attachment)
        raise MissingRecordError(detail=f"No attachment found with ID: {attachment_id}", entity_name="attachment")

    def list(self, entity_id: Optional[str], session: Optional[ClientSession] = None) -> list[AttachmentOut]:
        """
        Retrieve attachments from a MongoDB database.

        :param entity_id: The ID of the entity to filter attachments by.
        :param session: PyMongo ClientSession to use for database operations.
        :return: List of attachments or an empty list if no attachments are retrieved.
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

        message = "Retrieving all attachments from the database"
        if not query:
            logger.info(message)
        else:
            logger.info("%s matching the provided filter(s)", message)
            logger.debug("Provided filter(s): %s", query)

        # pylint: enable=duplicate-code

        attachments = self._attachments_collection.find(query, session=session)
        return [AttachmentOut(**attachment) for attachment in attachments]

    def update(self, attachment_id: str, attachment: AttachmentIn, session: ClientSession = None) -> AttachmentOut:
        """
        Updates an attachment by its ID in a MongoDB database.

        :param attachment_id: The ID of the attachment to update.
        :param attachment: The attachment containing the update data.
        :param session: PyMongo ClientSession to use for database operations.
        :return: The updated attachment.
        :raises InvalidObjectIdError: If the supplied `attachment_id` is invalid.
        """

        try:
            attachment_id = CustomObjectId(attachment_id)
        except InvalidObjectIdError as exc:
            exc.status_code = 404
            exc.response_detail = "Attachment not found"
            raise exc

        logger.info("Updating attachment metadata with ID: %s", attachment_id)

        stored_attachment = self.get(str(attachment_id), session=session)
        if attachment.file_name != stored_attachment.file_name and self._is_duplicate(
            attachment.entity_id, attachment.code, attachment_id, session=session
        ):
            raise DuplicateRecordError("Duplicate image found within the parent entity", entity_name="image")

        logger.info("Updating attachment metadata with ID: %s", attachment_id)
        self._attachments_collection.update_one(
            {"_id": attachment_id}, {"$set": attachment.model_dump(by_alias=True)}, session=session
        )

        return self.get(attachment_id=str(attachment_id), session=session)

    def delete(self, attachment_id: str, session: Optional[ClientSession] = None) -> None:
        """
        Delete an attachment by its ID from a MongoDB database.

        :param attachment_id: The ID of the attachment to delete.
        :param session: PyMongo ClientSession to use for database operations.
        :raises MissingRecordError: If the supplied `attachment_id` is non-existent.
        :raises InvalidObjectIdError: If the supplied `attachment_id` is invalid.
        """
        logger.info("Deleting attachment with ID: %s from the database", attachment_id)
        try:
            attachment_id = CustomObjectId(attachment_id)
        except InvalidObjectIdError as exc:
            exc.status_code = 404
            exc.response_detail = "Attachment not found"
            raise exc
        response = self._attachments_collection.delete_one(filter={"_id": attachment_id}, session=session)
        if response.deleted_count == 0:
            raise MissingRecordError(f"No attachment found with ID: {attachment_id}", entity_name="attachment")

    def delete_by_entity_id(self, entity_id: str, session: Optional[ClientSession] = None) -> None:
        """
        Delete attachments by entity ID.

        :param entity_id: The entity ID of the attachments to delete.
        :param session: PyMongo ClientSession to use for database operations.
        """
        logger.info("Deleting attachments with entity ID: %s from the database", entity_id)
        try:
            entity_id = CustomObjectId(entity_id)
            # Given it is deleting multiple, we are not raising an exception if no attachments were found to be deleted
            self._attachments_collection.delete_many(filter={"entity_id": entity_id}, session=session)
        except InvalidObjectIdError:
            # As this method takes in an entity_id to delete multiple attachments, and to hide the database behaviour,
            # we treat any invalid entity_id the same as a valid one that has no attachments associated to it.
            pass

    def count_by_entity_id(self, entity_id: str, session: Optional[ClientSession] = None) -> int:
        """
        Count the number of attachments matching the provided entity ID in a MongoDB database.

        :param entity_id: The entity ID to use to select which documents to count.
        :param session: PyMongo ClientSession to use for database operations.
        """
        logger.info("Counting number of attachments with entity ID: %s in the database", entity_id)
        return self._attachments_collection.count_documents(
            filter={"entity_id": CustomObjectId(entity_id)}, session=session
        )

    def _is_duplicate(
        self,
        entity_id: CustomObjectId,
        code: str,
        attachment_id: Optional[CustomObjectId] = None,
        session: Optional[ClientSession] = None,
    ) -> bool:
        """
        Check if an attachment with the same code already exists for the same entity.

        :param entity_id: ID of the entity.
        :param code: Code of the attachment to check for duplicates.
        :param attachment_id: ID of the attachment to check if the duplicate attachment found is itself.
        :param session: PyMongo ClientSession to use for database operations
        :return: `True` if a duplicate attachment code is found, `False` otherwise.
        """
        logger.info(
            "Checking if attachment with code '%s' already exists within the entity with id '%s'", code, entity_id
        )

        return (
            self._attachments_collection.find_one(
                {"entity_id": entity_id, "code": code, "_id": {"$ne": attachment_id}},
                session=session,
            )
            is not None
        )
