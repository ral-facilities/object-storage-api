"""
Unit tests for the `AttachmentStore` store.
"""

from test.mock_data import ATTACHMENT_POST_DATA_ALL_VALUES
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId

from object_storage_api.core.object_store import object_storage_config
from object_storage_api.schemas.attachment import AttachmentPostSchema
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


class CreatePresignedURLDSL(AttachmentStoreDSL):
    """Base class for `create` tests."""

    _attachment_post: AttachmentPostSchema
    _attachment_id: str
    _expected_object_key: str
    _expected_url: str
    _obtained_object_key: str
    _created_url: str

    def mock_create_presigned_url(self, attachment_post_data: dict) -> None:
        """
        Mocks object store methods appropriately to test the `create_presigned_url` store method.

        :param attachment_post_data: Dictionary containing the attachment data as would be required for an
                                     `AttachmentPost` schema.
        """
        self._attachment_post = AttachmentPostSchema(**attachment_post_data)
        self._attachment_id = str(ObjectId())

        self._expected_object_key = f"attachments/{self._attachment_post.entity_id}/{self._attachment_id}"

        # Mock presigned url generation
        self._expected_url = "http://test-url.com"
        self.mock_s3_client.generate_presigned_url.return_value = self._expected_url

    def call_create_presigned_url(self) -> None:
        """Calls the `AttachmentStore` `create_presigned_url` method with the appropriate data from a prior call to
        `mock_create_presigned_url`."""

        self._obtained_object_key, self._created_url = self.attachment_store.create_presigned_url(
            self._attachment_id, self._attachment_post
        )

    def check_create_presigned_url_success(self) -> None:
        """Checks that a prior call to `call_create_presigned_url` worked as expected."""

        self.mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": self._expected_object_key,
                "ContentType": "multipart/form-data",
            },
            ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
        )

        # Cannot know the expected creation and modified time here, so ignore in comparison
        assert self._obtained_object_key == self._expected_object_key
        assert self._created_url == self._expected_url


class TestCreatePresignedURL(CreatePresignedURLDSL):
    """Tests for creating a presigned URL for an attachment."""

    def test_create_presigned_url(self):
        """Test creating a presigned URL for an attachment."""

        self.mock_create_presigned_url(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.call_create_presigned_url()
        self.check_create_presigned_url_success()
