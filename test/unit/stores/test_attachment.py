"""
Unit tests for the `AttachmentStore` store.
"""

from test.mock_data import ATTACHMENT_POST_DATA_ALL_VALUES
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.core.object_store import object_storage_config
from object_storage_api.models.attachment import AttachmentIn
from object_storage_api.schemas.attachment import AttachmentPostSchema
from object_storage_api.stores.attachment import AttachmentStore


class AttachmentStoreDSL:
    """Base class for `AttachmentStore` unit tests."""

    mock_s3_client: MagicMock
    mock_object_id: MagicMock
    attachment_store: AttachmentStore

    @pytest.fixture(autouse=True)
    def setup(
        self,
        # Ensures all created and modified times are mocked throughout
        # pylint: disable=unused-argument
        model_mixins_datetime_now_mock,
    ):
        """Setup fixtures"""

        with patch("object_storage_api.stores.attachment.s3_client") as s3_client_mock:
            with patch("object_storage_api.stores.attachment.ObjectId") as object_id_mock:
                self.mock_s3_client = s3_client_mock
                self.mock_object_id = object_id_mock
                self.attachment_store = AttachmentStore()
                yield


class CreateDSL(AttachmentStoreDSL):
    """Base class for `create` tests."""

    _attachment_post: AttachmentPostSchema
    _expected_attachment_in: AttachmentIn
    _expected_url: str
    _created_attachment_in: AttachmentIn
    _generated_url: str
    _create_exception: pytest.ExceptionInfo

    def mock_create(self, attachment_post_data: dict) -> None:
        """
        Mocks object store methods appropriately to test the `create` store method.

        :param attachment_post_data: Dictionary containing the attachment data as would be required for an
                                     `AttachmentPost` schema.
        """
        self._attachment_post = AttachmentPostSchema(**attachment_post_data)

        attachment_id = ObjectId()
        self.mock_object_id.return_value = attachment_id

        expected_object_key = f"attachments/{self._attachment_post.entity_id}/{attachment_id}"

        # Mock presigned url generation
        self._expected_url = "http://test-url.com"
        self.mock_s3_client.generate_presigned_url.return_value = self._expected_url

        # Expected model data with the object key defined (Ignore if invalid to avoid a premature error)
        if self._attachment_post.entity_id != "invalid-id":
            self._expected_attachment_in = AttachmentIn(
                **self._attachment_post.model_dump(), id=str(attachment_id), object_key=expected_object_key
            )

    def call_create(self) -> None:
        """Calls the `AttachmentStore` `create` method with the appropriate data from a prior call to `mock_create`."""

        self._created_attachment_in, self._generated_url = self.attachment_store.create(self._attachment_post)

    def call_create_expecting_error(self, error_type: type[BaseException]) -> None:
        """
        Calls the `AttachmentStore` `create` method with the appropriate data from a prior call to `mock_create`
        while expecting an error to be raised.

        :param error_type: Expected exception to be raised.
        """

        with pytest.raises(error_type) as exc:
            self.attachment_store.create(self._attachment_post)
        self._create_exception = exc

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": self._expected_attachment_in.object_key,
                "ContentType": "multipart/form-data",
            },
            ExpiresIn=object_storage_config.presigned_url_expiry,
        )

        # Cannot know the expected creation and modified time here, so ignore in comparison
        assert self._created_attachment_in == self._expected_attachment_in
        assert self._generated_url == self._expected_url

    def check_create_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_create_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        """

        assert str(self._create_exception.value) == message


class TestCreate(CreateDSL):
    """Tests for creating an attachment."""

    def test_create(self):
        """Test creating an attachment."""

        self.mock_create(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.call_create()
        self.check_create_success()

    def test_create_with_invalid_entity_id(self):
        """Test creating an attachment with an invalid `entity_id`."""

        self.mock_create({**ATTACHMENT_POST_DATA_ALL_VALUES, "entity_id": "invalid-id"})
        self.call_create_expecting_error(InvalidObjectIdError)
        self.check_create_failed_with_exception("Invalid ObjectId value 'invalid-id'")
