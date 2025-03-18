"""
Module for custom exception classes.
"""

# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?


from typing import Optional


class BaseAPIException(Exception):
    """Base exception for API errors."""

    # Status code to return if this exception is raised
    status_code: int

    # Generic detail of the exception (That may be returned in a response)
    response_detail: str

    detail: str

    def __init__(self, detail: str, response_detail: Optional[str] = None):
        """
        Initialise the exception.

        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        :param response_detail: Generic detail of the exception that will be returned in a response.
        """
        super().__init__(detail)

        self.detail = detail

        if response_detail is not None:
            self.response_detail = response_detail


class DatabaseError(BaseAPIException):
    """Database related error."""


class InvalidObjectIdError(DatabaseError):
    """The provided value is not a valid ObjectId."""

    status_code = 422
    response_detail = "Invalid ID given"


class InvalidImageFileError(BaseAPIException):
    """The provided image file is not valid."""

    status_code = 422
    response_detail = "File given is not a valid image"


class InvalidFilenameExtension(BaseAPIException):
    """The provided filename's extension does not match expected file type."""

    status_code = 422
    response_detail = "Filename does not contain the correct extension"


class AttachmentUploadLimitReached(BaseAPIException):
    """The limit for the maximum number of attachments for the provided `entity_id` has been reached."""

    status_code = 422
    response_detail = "Limit for the maximum number of attachments for the provided `entity_id` has been reached"


class ImageUploadLimitReached(BaseAPIException):
    """The limit for the maximum number of images for the provided `entity_id` has been reached."""

    status_code = 422
    response_detail = "Limit for the maximum number of images for the provided `entity_id` has been reached"


class MissingRecordError(DatabaseError):
    """A specific database record was requested but could not be found."""

    status_code = 404
    response_detail = "Requested record was not found"

    def __init__(self, detail: str, response_detail: Optional[str] = None, entity_name: Optional[str] = None):
        """
        Initialise the exception.

        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        :param response_detail: Generic detail of the exception to be returned in the response.
        :param entity_name: Name of the entity to include in the response detail.
        """
        super().__init__(detail, response_detail)

        if entity_name is not None:
            self.response_detail = f"{entity_name.capitalize()} not found"
