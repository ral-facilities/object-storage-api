"""
Mock data for use in tests.

Names should ideally be descriptive enough to recognise what they are without looking at the data itself.
Letters may be appended in places to indicate the data is of the same type, but has different specific values
to others.

_POST_DATA - Is for a `PostSchema` schema.
_POST_RESPONSE_DATA - Is for a `PostResponseSchema` schema.
_IN_DATA - Is for an `In` model.
_GET_DATA - Is for an entity schema - Used in assertions for e2e tests.
_DATA - Is none of the above - likely to be used in post requests as they are likely identical, only with some ids
        missing so that they can be added later e.g. for pairing up units that aren't known before hand.
"""

from unittest.mock import ANY

from bson import ObjectId

# Used for _GET_DATA's as when comparing these will not be possible to know at runtime
CREATED_MODIFIED_GET_DATA_EXPECTED = {"created_time": ANY, "modified_time": ANY}

# ---------------------------- ATTACHMENTS -----------------------------

# Required values only

ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY = {
    "entity_id": str(ObjectId()),
    "file_name": "report.txt",
}

ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY = {
    **ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY,
    **CREATED_MODIFIED_GET_DATA_EXPECTED,
    "id": ANY,
    "upload_url": ANY,
    "title": None,
    "description": None,
}

# All values

ATTACHMENT_POST_DATA_ALL_VALUES = {
    "entity_id": str(ObjectId()),
    "file_name": "report.txt",
    "title": "Report Title",
    "description": "A damage report.",
}

ATTACHMENT_IN_DATA_ALL_VALUES = {
    **ATTACHMENT_POST_DATA_ALL_VALUES,
    "id": str(ObjectId()),
    "object_key": "attachments/65df5ee771892ddcc08bd28f/65e0a624d64aaae884abaaee",
}
