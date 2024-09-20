"""
Module for providing a repository for managing attachments in a MongoDB database.
"""

import logging
from typing import Collection

from object_storage_api.core.database import DatabaseDep

logger = logging.getLogger()


class AttachmentRepo:
    """
    Repository for managing attachments in a MongoDB database.
    """

    def __init__(self, database: DatabaseDep) -> None:
        """
        Initialise the `SystemRepo` with a MongoDB database instance.

        :param database: Database to use.
        """
        self._database = database
        self._attachments_collection: Collection = self._database.attachments
