"""
Unit tests for the `AttachmentService` service.
"""

from test.mock_data import ATTACHMENT_POST_DATA_ALL_VALUES
from unittest.mock import MagicMock, Mock, patch

import pytest
from bson import ObjectId

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.models.attachment import AttachmentIn, AttachmentOut
from object_storage_api.schemas.attachment import (
    AttachmentPostResponseSchema,
    AttachmentPostSchema,
    AttachmentPostUploadInfoSchema,
)
from object_storage_api.services.attachment import AttachmentService


class AttachmentServiceDSL:
    """Base class for `AttachmentService` unit tests."""

    mock_attachment_repository: Mock
    mock_attachment_store: Mock
    attachment_service: AttachmentService

    mock_object_id: MagicMock

    @pytest.fixture(autouse=True)
    def setup(
        self,
        attachment_repository_mock,
        attachment_store_mock,
        attachment_service,
        # Ensures all created and modified times are mocked throughout
        # pylint: disable=unused-argument
        model_mixins_datetime_now_mock,
    ):
        """Setup fixtures"""

        self.mock_attachment_repository = attachment_repository_mock
        self.mock_attachment_store = attachment_store_mock
        self.attachment_service = attachment_service

        with patch("object_storage_api.services.attachment.ObjectId") as object_id_mock:
            self.mock_object_id = object_id_mock
            yield


class CreateDSL(AttachmentServiceDSL):
    """Base class for `create` tests."""

    _attachment_post: AttachmentPostSchema
    _expected_attachment_id: ObjectId
    _expected_attachment_in: AttachmentIn
    _expected_attachment: AttachmentPostResponseSchema
    _created_attachment: AttachmentPostResponseSchema
    _create_exception: pytest.ExceptionInfo

    def mock_create(self, attachment_post_data: dict) -> None:
        """
        Mocks repo & store methods appropriately to test the `create` service method.

        :param attachment_post_data: Dictionary containing the basic attachment data as would be required for a
                                     `AttachmentPostSchema` (i.e. no created and modified times required).
        """

        self._attachment_post = AttachmentPostSchema(**attachment_post_data)

        self._expected_attachment_id = ObjectId()
        self.mock_object_id.return_value = self._expected_attachment_id

        # Store
        expected_object_key = "some/object/key"
        expected_upload_info = AttachmentPostUploadInfoSchema(
            url="http://example-upload-url", fields={"some": "fields"}
        )
        self.mock_attachment_store.create_presigned_post.return_value = (expected_object_key, expected_upload_info)

        # Expected model data with the object key defined (Ignore if invalid to avoid a premature error)
        if self._attachment_post.entity_id != "invalid-id":
            self._expected_attachment_in = AttachmentIn(
                **self._attachment_post.model_dump(),
                id=str(self._expected_attachment_id),
                object_key=expected_object_key,
            )

            # Repo (The contents of the returned output model does not matter here as long as its valid)
            expected_attachment_out = AttachmentOut(**self._expected_attachment_in.model_dump(by_alias=True))
            self.mock_attachment_repository.create.return_value = expected_attachment_out

            self._expected_attachment = AttachmentPostResponseSchema(
                **expected_attachment_out.model_dump(), upload_info=expected_upload_info
            )

    def call_create(self) -> None:
        """Calls the `AttachmentService` `create` method with the appropriate data from a prior call to
        `mock_create`."""

        self._created_attachment = self.attachment_service.create(self._attachment_post)

    def call_create_expecting_error(self, error_type: type[BaseException]) -> None:
        """Calls the `AttachmentService` `create` method with the appropriate data from a prior call to
        `mock_create` while expecting an error to be raised..

        :param error_type: Expected exception to be raised.
        """

        with pytest.raises(error_type) as exc:
            self.attachment_service.create(self._attachment_post)
        self._create_exception = exc

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.mock_attachment_store.create_presigned_post.assert_called_once_with(
            str(self._expected_attachment_id), self._attachment_post
        )
        self.mock_attachment_repository.create.assert_called_once_with(self._expected_attachment_in)

        assert self._created_attachment == self._expected_attachment

    def check_create_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_create_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        """

        self.mock_attachment_store.create_presigned_post.assert_called_once_with(
            str(self._expected_attachment_id), self._attachment_post
        )
        self.mock_attachment_repository.create.assert_not_called()

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
