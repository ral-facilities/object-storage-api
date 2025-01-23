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

# ---------------------------- GENERAL -----------------------------

# Used for _GET_DATA's as when comparing these will not be possible to know at runtime
CREATED_MODIFIED_GET_DATA_EXPECTED = {"created_time": ANY, "modified_time": ANY}

# ---------------------------- AUTHENTICATION -----------------------------

# pylint:disable=fixme
# TODO: The below access tokens are identical to the ones in inventory-management-system-api - Use common repo?

VALID_ACCESS_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXJuYW1lIiwiZXhwIjoyNTM0MDIzMDA3OTl9.bagU2Wix8wKzydVU_L3Z"
    "ZuuMAxGxV4OTuZq_kS2Fuwm839_8UZOkICnPTkkpvsm1je0AWJaIXLGgwEa5zUjpG6lTrMMmzR9Zi63F0NXpJqQqoOZpTBMYBaggsXqFkdsv-yAKUZ"
    "8MfjCEyk3UZ4PXZmEcUZcLhKcXZr4kYJPjio2e5WOGpdjK6q7s-iHGs9DQFT_IoCnw9CkyOKwYdgpB35hIGHkNjiwVSHpyKbFQvzJmIv5XCTSRYqq0"
    "1fldh-QYuZqZeuaFidKbLRH610o2-1IfPMUr-yPtj5PZ-AaX-XTLkuMqdVMCk0_jeW9Os2BPtyUDkpcu1fvW3_S6_dK3nQ"
)

VALID_ACCESS_TOKEN_MISSING_USERNAME = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjI1MzQwMjMwMDc5OX0.h4Hv_sq4-ika1rpuRx7k3pp0cF_BZ65WVSbIHS7oh9SjPpGHt"
    "GhVHU1IJXzFtyA9TH-68JpAZ24Dm6bXbH6VJKoc7RCbmJXm44ufN32ga7jDqXH340oKvi_wdhEHaCf2HXjzsHHD7_D6XIcxU71v2W5_j8Vuwpr3SdX"
    "6ea_yLIaCDWynN6FomPtUepQAOg3c7DdKohbJD8WhKIDV8UKuLtFdRBfN4HEK5nNs0JroROPhcYM9L_JIQZpdI0c83fDFuXQC-cAygzrSnGJ6O4DyS"
    "cNL3VBNSmNTBtqYOs1szvkpvF9rICPgbEEJnbS6g5kmGld3eioeuDJIxeQglSbxog"
)

EXPIRED_ACCESS_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXJuYW1lIiwiZXhwIjotNjIxMzU1OTY4MDB9.G_cfC8PNYE5yERyyQNRk"
    "9mTmDusU_rEPgm7feo2lWQF6QMNnf8PUN-61FfMNRVE0QDSvAmIMMNEOa8ma0JHZARafgnYJfn1_FSJSoRxC740GpG8EFSWrpM-dQXnoD263V9FlK-"
    "On6IbhF-4Rh9MdoxNyZk2Lj7NvCzJ7gbgbgYM5-sJXLxB-I5LfMfuYM3fx2cRixZFA153l46tFzcMVBrAiBxl_LdyxTIOPfHF0UGlaW2UtFi02gyBU"
    "4E4wTOqPc4t_CSi1oBSbY7h9O63i8IU99YsOCdvZ7AD3ePxyM1xJR7CFHycg9Z_IDouYnJmXpTpbFMMl7SjME3cVMfMrAQ"
)

INVALID_ACCESS_TOKEN = VALID_ACCESS_TOKEN + "1"

# ---------------------------- ATTACHMENTS -----------------------------

# Used for _POST_RESPONSE_DATA's as when comparing most of these are not possible to know at runtime arguably we dont
# need to put the fields in but it ensures we capture potential changes to how boto3 functions
ATTACHMENT_UPLOAD_INFO_POST_RESPONSE_DATA_EXPECTED = {
    "upload_info": {
        "url": ANY,
        "fields": {
            "AWSAccessKeyId": ANY,
            "Content-Type": "multipart/form-data",
            "key": ANY,
            "policy": ANY,
            "signature": ANY,
        },
    }
}

# Required values only

ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY = {
    "entity_id": str(ObjectId()),
    "file_name": "report.txt",
}

ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY = {
    **ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY,
    **CREATED_MODIFIED_GET_DATA_EXPECTED,
    **ATTACHMENT_UPLOAD_INFO_POST_RESPONSE_DATA_EXPECTED,
    "id": ANY,
    "title": None,
    "description": None,
}

# All values

ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES = {
    "title": "Shattered Laser",
    "description": "A text attachment describing damage to a laser.",
    "file_name": "laserDamage.txt",
}

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

ATTACHMENT_GET_METADATA_REQUIRED_VALUES_ONLY = {
    **ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY,
    "id": ANY,
}

ATTACHMENT_GET_DATA_REQUIRED_VALUES_ONLY = {
    **ATTACHMENT_GET_METADATA_REQUIRED_VALUES_ONLY,
    "url": ANY,
}

ATTACHMENT_GET_METADATA_ALL_VALUES = {
    **ATTACHMENT_POST_DATA_ALL_VALUES,
    "id": ANY,
}

ATTACHMENT_GET_DATA_ALL_VALUES = {
    **ATTACHMENT_GET_METADATA_ALL_VALUES,
    "download_url": ANY,
}

ATTACHMENT_GET_METADATA_DATA_ALL_VALUES_AFTER_PATCH = {
    **ATTACHMENT_GET_METADATA_ALL_VALUES,
    **ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES,
}

ATTACHMENT_POST_RESPONSE_DATA_ALL_VALUES = {
    **ATTACHMENT_GET_METADATA_ALL_VALUES,
    **CREATED_MODIFIED_GET_DATA_EXPECTED,
    **ATTACHMENT_UPLOAD_INFO_POST_RESPONSE_DATA_EXPECTED,
}

# ---------------------------- IMAGES -----------------------------

IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY = {
    "entity_id": str(ObjectId()),
}

IMAGE_GET_METADATA_DATA_REQUIRED_VALUES_ONLY = {
    **IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY,
    **CREATED_MODIFIED_GET_DATA_EXPECTED,
    "id": ANY,
    "file_name": "image.jpg",
    "primary": False,
    "thumbnail_base64": "UklGRjQAAABXRUJQVlA4ICgAAADQAQCdASoCAAEAAUAmJYwCdAEO/gOOAAD+qlQWHDxhNJOjVlqIb8AA",
    "title": None,
    "description": None,
}

IMAGE_GET_DATA_REQUIRED_VALUES_ONLY = {
    **IMAGE_GET_METADATA_DATA_REQUIRED_VALUES_ONLY,
    "url": ANY,
}


IMAGE_PATCH_METADATA_DATA_ALL_VALUES = {
    "title": "Shattered Laser",
    "description": "An image of a shattered laser.",
    "file_name": "picture.jpg",
    "primary": False,
}

IMAGE_POST_METADATA_DATA_ALL_VALUES = {
    **IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY,
    "title": "Report Title",
    "description": "A damage report.",
}


IMAGE_IN_DATA_ALL_VALUES = {
    **IMAGE_POST_METADATA_DATA_ALL_VALUES,
    "id": str(ObjectId()),
    "file_name": "image.jpg",
    "object_key": "images/65df5ee771892ddcc08bd28f/65e0a624d64aaae884abaaee",
    "thumbnail_base64": "UklGRjQAAABXRUJQVlA4ICgAAADQAQCdASoCAAEAAUAmJYwCdAEO/gOOAAD+qlQWHDxhNJOjVlqIb8AA",
}

IMAGE_GET_METADATA_DATA_ALL_VALUES = {
    **IMAGE_POST_METADATA_DATA_ALL_VALUES,
    **CREATED_MODIFIED_GET_DATA_EXPECTED,
    "id": ANY,
    "file_name": "image.jpg",
    "primary": False,
    "thumbnail_base64": "UklGRjQAAABXRUJQVlA4ICgAAADQAQCdASoCAAEAAUAmJYwCdAEO/gOOAAD+qlQWHDxhNJOjVlqIb8AA",
}

IMAGE_GET_METADATA_DATA_ALL_VALUES_AFTER_PATCH = {
    **IMAGE_GET_METADATA_DATA_ALL_VALUES,
    **IMAGE_PATCH_METADATA_DATA_ALL_VALUES,
}

IMAGE_GET_DATA_ALL_VALUES = {
    **IMAGE_GET_METADATA_DATA_ALL_VALUES,
    "url": ANY,
}
