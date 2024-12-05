"""
Module for defining the API schema models for representing images.
"""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from object_storage_api.schemas.mixins import CreatedModifiedSchemaMixin


class ImagePatchMetadataSchema(BaseModel):
    """
    Base schema model for an image.
    """

    title: Optional[str] = Field(default=None, description="Title of the image")
    description: Optional[str] = Field(default=None, description="Description of the image")


class ImagePostMetadataSchema(ImagePatchMetadataSchema):
    """Base schema model for an image."""

    entity_id: str = Field(description="ID of the entity the image relates to")


class ImageMetadataSchema(CreatedModifiedSchemaMixin, ImagePostMetadataSchema):
    """Schema model for an image's metadata."""

    id: str = Field(description="ID of the image")
    file_name: str = Field(description="File name of the image")
    primary: bool = Field(description="Whether the image is the primary for its related entity")
    thumbnail_base64: str = Field(description="Thumbnail of the image as a base64 encoded byte string")


class ImageSchema(ImageMetadataSchema):
    """Schema model for an image get request response."""

    url: HttpUrl = Field(description="Presigned get URL to get the image file")
