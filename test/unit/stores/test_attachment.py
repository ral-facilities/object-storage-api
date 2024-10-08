"""
Unit tests for the `AttachmentStore` store.
"""

from test.mock_data import ATTACHMENT_POST_DATA_ALL_VALUES
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId

from object_storage_api.core.config import config
from object_storage_api.core.object_store import object_storage_config
from object_storage_api.schemas.attachment import AttachmentPostSchema, AttachmentPostUploadInfoSchema
from object_storage_api.stores.attachment import AttachmentStore


class AttachmentStoreDSL:
    """Base class for `AttachmentStore` unit tests."""

    mock_s3_client: MagicMock
    attachment_store: AttachmentStore

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup fixtures"""

        with patch("object_storage_api.stores.attachment.s3_client") as s3_client_mock:
            self.mock_s3_client = s3_client_mock
            self.attachment_store = AttachmentStore()
            yield


class CreatePresignedPostDSL(AttachmentStoreDSL):
    """Base class for `create_presigned_post` tests."""

    _attachment_post: AttachmentPostSchema
    _attachment_id: str
    _expected_object_key: str
    _expected_attachment_upload_info: AttachmentPostUploadInfoSchema
    _obtained_object_key: str
    _created_attachment_upload_info: str

    def mock_create_presigned_post(self, attachment_post_data: dict) -> None:
        """
        Mocks object store methods appropriately to test the `create_presigned_post` store method.

        :param attachment_post_data: Dictionary containing the attachment data as would be required for an
                                     `AttachmentPostSchema`.
        """
        self._attachment_post = AttachmentPostSchema(**attachment_post_data)
        self._attachment_id = str(ObjectId())

        self._expected_object_key = f"attachments/{self._attachment_post.entity_id}/{self._attachment_id}"

        # Mock presigned post generation
        expected_presigned_post_response = {"url": "http://example-upload-url", "fields": {"some": "fields"}}
        self._expected_attachment_upload_info = AttachmentPostUploadInfoSchema(**expected_presigned_post_response)
        self.mock_s3_client.generate_presigned_post.return_value = expected_presigned_post_response

    def call_create_presigned_post(self) -> None:
        """Calls the `AttachmentStore` `create_presigned_post` method with the appropriate data from a prior call to
        `mock_create_presigned_post`."""

        self._obtained_object_key, self._created_attachment_upload_info = self.attachment_store.create_presigned_post(
            self._attachment_id, self._attachment_post
        )

    def check_create_presigned_post_success(self) -> None:
        """Checks that a prior call to `call_create_presigned_post` worked as expected."""

        self.mock_s3_client.generate_presigned_post.assert_called_once_with(
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=self._expected_object_key,
            Fields={"Content-Type": "multipart/form-data"},
            Conditions=[
                ["content-length-range", 0, config.attachment.max_size_bytes],
                ["eq", "$Content-Type", "multipart/form-data"],
            ],
            ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
        )

        assert self._obtained_object_key == self._expected_object_key
        assert self._created_attachment_upload_info == self._expected_attachment_upload_info


class TestCreatePresignedPost(CreatePresignedPostDSL):
    """Tests for creating a presigned post for an attachment."""

    def test_create_presigned_post(self):
        """Test creating a presigned post for an attachment."""

        self.mock_create_presigned_post(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.call_create_presigned_post()
        self.check_create_presigned_post_success()
