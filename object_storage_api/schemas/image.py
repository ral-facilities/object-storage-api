"""
Module for defining the API schema models for representing images.
"""

from typing import Optional

from pydantic import BaseModel, Field

from object_storage_api.schemas.mixins import CreatedModifiedSchemaMixin


class ImagePostMetadataSchema(BaseModel):
    """
    Base schema model for an image.
    """

    entity_id: str = Field(description="ID of the entity the image relates to")
    title: Optional[str] = Field(default=None, description="Title of the image")
    description: Optional[str] = Field(default=None, description="Description of the image")


class ImageSchema(CreatedModifiedSchemaMixin, ImagePostMetadataSchema):
    """
    Schema model for an image get request response.
    """

    id: str = Field(description="ID of the image")
    file_name: str = Field(description="File name of the image")
