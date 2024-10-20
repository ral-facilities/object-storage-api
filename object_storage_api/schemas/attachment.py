"""
Module for defining the API schema models for representing attachments.
"""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from object_storage_api.schemas.mixins import CreatedModifiedSchemaMixin


class AttachmentPostSchema(BaseModel):
    """
    Schema model for an attachment creation request.
    """

    entity_id: str = Field(description="ID of the entity the attachment relates to")
    file_name: str = Field(description="File name of the attachment")
    title: Optional[str] = Field(default=None, description="Title of the attachment")
    description: Optional[str] = Field(default=None, description="Description of the attachment")


class AttachmentPostUploadInfoSchema(BaseModel):
    """
    Schema model for the information required to upload a file.
    """

    url: HttpUrl = Field(description="Pre-signed upload URL to upload the attachment file to")
    fields: dict = Field(description="Form fields required for submitting the attachment file upload request")


class AttachmentPostResponseSchema(CreatedModifiedSchemaMixin, AttachmentPostSchema):
    """
    Schema model for the response to an attachment creation request.
    """

    id: str = Field(description="ID of the attachment")
    upload_info: AttachmentPostUploadInfoSchema = Field(
        description="Information required to upload the attachment file"
    )
