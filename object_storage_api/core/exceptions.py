"""
Module for custom exception classes.
"""

# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?
# TODO: Try custom exception handler for these exceptions


class DatabaseError(Exception):
    """
    Database related error.
    """


class InvalidObjectIdError(DatabaseError):
    """
    The provided value is not a valid ObjectId.
    """
