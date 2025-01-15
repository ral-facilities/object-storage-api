"""
Module for providing a repository for managing attachments in a MongoDB database.
"""

import logging
from typing import Optional

from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from object_storage_api.core.custom_object_id import CustomObjectId
from object_storage_api.core.database import DatabaseDep
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

        logger.info("Inserting the new attachment into the database")
        result = self._attachments_collection.insert_one(attachment.model_dump(by_alias=True), session=session)
        return self.get(str(result.inserted_id), session=session)

    def get(self, attachment_id: str, session: Optional[ClientSession] = None) -> Optional[AttachmentOut]:
        """
        Retrieve an attachment by its ID from a MongoDB database.

        :param attachment_id: ID of the attachment to retrieve.
        :param session: PyMongo ClientSession to use for database operations.
        :return: Retrieved attachment or `None` if not found.
        """
        attachment_id = CustomObjectId(attachment_id)
        logger.info("Retrieving attachment with ID: %s from the database", attachment_id)
        attachment = self._attachments_collection.find_one({"_id": attachment_id}, session=session)
        if attachment:
            return AttachmentOut(**attachment)
        return None

    def list(self, entity_id: Optional[str], session: Optional[ClientSession] = None) -> list[AttachmentOut]:
        """
        Retrieve attachments from a MongoDB database.

        :param session: PyMongo ClientSession to use for database operations.
        :param entity_id: The ID of the entity to filter attachments by.
        :return: List of attachments or an empty list if no attachments are retrieved.
        """

        # There is some duplicate code here, due to the attachments and images methods being very similar
        # pylint: disable=duplicate-code

        query = {}
        if entity_id is not None:
            query["entity_id"] = CustomObjectId(entity_id)

        message = "Retrieving all attachments from the database"
        if not query:
            logger.info(message)
        else:
            logger.info("%s matching the provided filter(s)", message)
            logger.debug("Provided filter(s): %s", query)

        # pylint: enable=duplicate-code

        attachments = self._attachments_collection.find(query, session=session)
        return [AttachmentOut(**attachment) for attachment in attachments]
