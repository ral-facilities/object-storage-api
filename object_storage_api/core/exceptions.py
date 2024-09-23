"""
Module for custom exception classes.
"""

# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?


class BaseAPIException(Exception):
    """
    Base exception for API errors.
    """

    # Status code to return if this exception is raised
    status_code: int

    # Generic detail of the exception (That may be returned in a response)
    response_detail: str

    detail: str

    def __init__(self, detail: str):
        """
        Initialise the exception.

        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        """
        super().__init__(detail)

        self.detail = detail


class DatabaseError(BaseAPIException):
    """
    Database related error.
    """


class InvalidObjectIdError(DatabaseError):
    """
    The provided value is not a valid ObjectId.
    """

    status_code = 422
    response_detail = "Invalid ID given"
