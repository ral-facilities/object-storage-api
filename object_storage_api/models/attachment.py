"""
Module for defining the database models for representing attachments
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from object_storage_api.models.custom_object_id_data_types import CustomObjectIdField, StringObjectIdField


class AttachmentIn(BaseModel):
    """
    Input database model for an attachment.
    """

    entity_id: CustomObjectIdField
    file_name: str
    title: Optional[str] = None
    description: Optional[str] = None


class AttachmentOut(AttachmentIn):
    """
    Output database model for an attachment.
    """

    id: StringObjectIdField = Field(alias="_id")
    entity_id: StringObjectIdField

    model_config = ConfigDict(populate_by_name=True)
