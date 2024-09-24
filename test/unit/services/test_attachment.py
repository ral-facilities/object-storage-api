"""
Unit tests for the `AttachmentService` service.
"""

from test.mock_data import ATTACHMENT_POST_DATA_ALL_VALUES
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId

from object_storage_api.models.attachment import AttachmentIn, AttachmentOut
from object_storage_api.schemas.attachment import AttachmentPostResponseSchema, AttachmentPostSchema
from object_storage_api.services.attachment import AttachmentService


class AttachmentServiceDSL:
    """Base class for `AttachmentService` unit tests."""

    mock_attachment_repository: Mock
    mock_attachment_store: Mock
    attachment_service: AttachmentService

    @pytest.fixture(autouse=True)
    def setup(
        self,
        attachment_repository_mock,
        attachment_store_mock,
        attachment_service,
    ):
        """Setup fixtures"""

        self.mock_attachment_repository = attachment_repository_mock
        self.mock_attachment_store = attachment_store_mock
        self.attachment_service = attachment_service


class CreateDSL(AttachmentServiceDSL):
    """Base class for `create` tests."""

    _attachment_post: AttachmentPostSchema
    _expected_attachment_in: MagicMock
    _expected_attachment: AttachmentPostResponseSchema
    _created_attachment: AttachmentPostResponseSchema

    def mock_create(self, attachment_post_data: dict) -> None:
        """
        Mocks repo & store methods appropriately to test the `create` service method.

        :param attachment_post_data: Dictionary containing the basic attachment data as would be required for a
                                     `AttachmentPostSchema` (i.e. no created and modified times required).
        """

        self._attachment_post = AttachmentPostSchema(**attachment_post_data)

        # Store
        self._expected_attachment_in = MagicMock()
        expected_upload_url = "http://example-upload-url"
        self.mock_attachment_store.create.return_value = (self._expected_attachment_in, expected_upload_url)

        # Repo (The contents of the returned output model does not matter here as long as its valid)
        expected_attachment_out = AttachmentOut(
            **AttachmentIn(**attachment_post_data, id=str(ObjectId()), object_key="some-object-key").model_dump(
                by_alias=True
            )
        )
        self.mock_attachment_repository.create.return_value = expected_attachment_out

        self._expected_attachment = AttachmentPostResponseSchema(
            **expected_attachment_out.model_dump(), upload_url=expected_upload_url
        )

    def call_create(self) -> None:
        """Calls the `AttachmentService` `create` method with the appropriate data from a prior call to
        `mock_create`."""

        self._created_attachment = self.attachment_service.create(self._attachment_post)

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.mock_attachment_store.create.assert_called_once_with(self._attachment_post)
        self.mock_attachment_repository.create.assert_called_once_with(self._expected_attachment_in)

        assert self._created_attachment == self._expected_attachment


class TestCreate(CreateDSL):
    """Tests for creating an attachment."""

    def test_create(self):
        """Test creating an attachment."""

        self.mock_create(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.call_create()
        self.check_create_success()
