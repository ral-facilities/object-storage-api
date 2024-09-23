"""
Module for custom exception classes.
"""

# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?


class BaseAPIException(Exception):
    """
    Base exception for API errors.
    """

    status_code: int
    detail: str
    response_detail: str

    def __init__(self, status_code: int, detail: str, response_detail: str):
        """
        Initialise the exception.

        :param status_code: Status code to return if this exception is raised.
        :param detail: Specific detail of the exception (just like Exception would take - this will only be logged
                       and not returned in a response).
        :param response_detail: General response detail to return in the response if this exception is raised.
        """
        super().__init__(detail)

        self.status_code = status_code
        self.detail = detail
        self.response_detail = response_detail


class DatabaseError(BaseAPIException):
    """
    Database related error.
    """


class InvalidObjectIdError(DatabaseError):
    """
    The provided value is not a valid ObjectId.
    """

    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail, response_detail="Invalid ID given")
