"""
Module for defining the schema mixins to be inherited from to provide specific fields
"""

from pydantic import AwareDatetime, BaseModel, Field

# pylint:disable=fixme
# TODO: This file is identical to the one in inventory-management-system-api - Use common repo?


class CreatedModifiedSchemaMixin(BaseModel):
    """
    Output schema mixin that provides creation and modified time fields
    """

    created_time: AwareDatetime = Field(description="The date and time this entity was created")
    modified_time: AwareDatetime = Field(description="The date and time this entity was last updated")
