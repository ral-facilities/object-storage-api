"""
Module for custom exception classes.
"""

# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?


from typing import Optional

from fastapi import status
from ims_common.exceptions import BaseAPIException


class DatabaseError(BaseAPIException):
    """Database related error."""


class InvalidObjectIdError(DatabaseError):
    """The provided value is not a valid ObjectId."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    response_detail = "Invalid ID given"


class InvalidImageFileError(BaseAPIException):
    """The provided image file is not valid."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    response_detail = "File given is not a valid image"


class FileTypeMismatchException(BaseAPIException):
    """The extension and content type of the provided file do not match."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    response_detail = "File extension and content type do not match"


class UnsupportedFileExtensionException(BaseAPIException):
    """The provided file extension is not supported."""

    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    response_detail = "File extension is not supported"


class UploadLimitReachedError(BaseAPIException):
    """The limit for the maximum number of attachments or images for the provided `entity_id` has been reached."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, detail: str, entity_type: str):
        """
        Initialise the exception.

        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        :param entity_type: Type of the entity to include in the response detail.
        """

        response_detail = (
            f"Limit for the maximum number of {entity_type}s for the provided `entity_id` has been reached"
        )
        super().__init__(detail, response_detail)


class MissingRecordError(DatabaseError):
    """A specific database record was requested but could not be found."""

    status_code = status.HTTP_404_NOT_FOUND
    response_detail = "Requested record was not found"

    def __init__(self, detail: str, response_detail: Optional[str] = None, entity_type: Optional[str] = None):
        """
        Initialise the exception.

        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        :param response_detail: Generic detail of the exception to be returned in the response.
        :param entity_type: Name of the entity to include in the response detail.
        """
        super().__init__(detail, response_detail)

        if entity_type is not None:
            self.response_detail = f"{entity_type.capitalize()} not found"


class DuplicateRecordError(DatabaseError):
    """The record being added to the database is a duplicate."""

    status_code = status.HTTP_409_CONFLICT
    response_detail = "Duplicate record found"

    def __init__(self, detail: str, response_detail: Optional[str] = None, entity_type: Optional[str] = None):
        """
        Initialise the exception.

        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        :param response_detail: Generic detail of the exception to be returned in the response.
        :param entity_type: Type of the entity to include in the response detail.
        """
        super().__init__(detail, response_detail)

        if entity_type is not None:
            self.response_detail = f"An {entity_type} with the same file name already exists within the parent entity."
