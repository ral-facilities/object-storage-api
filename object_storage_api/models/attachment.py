"""
Module for defining the database models for representing attachments.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from object_storage_api.models.custom_object_id_data_types import CustomObjectIdField, StringObjectIdField
from object_storage_api.models.mixins import CreatedModifiedTimeInMixin, CreatedModifiedTimeOutMixin


class AttachmentBase(BaseModel):
    """
    Base database model for an attachment.
    """

    file_name: str
    object_key: str
    title: Optional[str] = None
    description: Optional[str] = None


class AttachmentIn(CreatedModifiedTimeInMixin, AttachmentBase):
    """
    Input database model for an attachment.
    """

    # Because we need to generate an id before insertion into the database (to ensure we can store the correct
    # `object_key``) we must manually specify the id rather than relying on MongoDB to do it.
    id: CustomObjectIdField = Field(serialization_alias="_id")
    entity_id: CustomObjectIdField


class AttachmentOut(CreatedModifiedTimeOutMixin, AttachmentBase):
    """
    Output database model for an attachment.
    """

    id: StringObjectIdField = Field(alias="_id")
    entity_id: StringObjectIdField

    model_config = ConfigDict(populate_by_name=True)
