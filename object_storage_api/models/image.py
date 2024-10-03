"""
Module for defining the database models for representing images.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from object_storage_api.models.custom_object_id_data_types import CustomObjectIdField, StringObjectIdField
from object_storage_api.models.mixins import CreatedModifiedTimeInMixin, CreatedModifiedTimeOutMixin


class ImageBase(BaseModel):
    """
    Base database model for an image.
    """

    file_name: str
    # Key of the image file in object storage
    object_key: str
    title: Optional[str] = None
    description: Optional[str] = None


class ImageIn(CreatedModifiedTimeInMixin, ImageBase):
    """
    Input database model for an image.
    """

    # Because we need to generate an id before insertion into the database (to ensure we can store the correct
    # `object_key``) we must manually specify the id rather than relying on MongoDB to do it.
    id: CustomObjectIdField = Field(serialization_alias="_id")
    entity_id: CustomObjectIdField


class ImageOut(CreatedModifiedTimeOutMixin, ImageBase):
    """
    Output database model for an image.
    """

    id: StringObjectIdField = Field(alias="_id")
    entity_id: StringObjectIdField

    model_config = ConfigDict(populate_by_name=True)
