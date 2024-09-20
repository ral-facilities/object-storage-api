"""
Module for defining the API schema models for representing Attachments
"""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class AttachmentPostSchema(BaseModel):
    """
    Schema model for an attachment creation request
    """

    entity_id: str = Field(description="ID of the entity the attachment relates to")
    title: Optional[str] = Field(default=None, description="Title of the attachment")
    description: Optional[str] = Field(default=None, description="Description of the attachment")
    file_name: str = Field(description="File name of the attachment")


class AttachmentPostResponseSchema(AttachmentPostSchema):
    """
    Schema model for the response to an attachment creation request
    """

    id: str = Field(description="ID of the attachment")
    upload_url: HttpUrl = Field(description="Pre-signed upload URL to upload the attachment file to")
