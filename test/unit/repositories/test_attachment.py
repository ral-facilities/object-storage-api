"""
Unit tests for the `AttachmentRepo` repository.
"""

from test.mock_data import ATTACHMENT_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from unittest.mock import MagicMock, Mock

import pytest

from object_storage_api.models.attachment import AttachmentIn, AttachmentOut
from object_storage_api.repositories.attachment import AttachmentRepo


class AttachmentRepoDSL:
    """Base class for `AttachmentRepo` unit tests."""

    mock_database: Mock
    attachment_repository: AttachmentRepo
    attachments_collection: Mock

    mock_session = MagicMock()

    @pytest.fixture(autouse=True)
    def setup(self, database_mock):
        """Setup fixtures"""

        self.mock_database = database_mock
        self.attachment_repository = AttachmentRepo(database_mock)
        self.attachments_collection = database_mock.attachments


class CreateDSL(AttachmentRepoDSL):
    """Base class for `create` tests."""

    _attachment_in: AttachmentIn
    _expected_attachment_out: AttachmentOut
    _created_attachment: AttachmentOut
    _create_exception: pytest.ExceptionInfo

    def mock_create(
        self,
        attachment_in_data: dict,
    ) -> None:
        """
        Mocks database methods appropriately to test the `create` repo method.

        :param attachment_in_data: Dictionary containing the attachment data as would be required for a `AttachmentIn`
                                   database model (i.e. no created and modified times required).
        """

        # Pass through `AttachmentIn` first as need creation and modified times
        self._attachment_in = AttachmentIn(**attachment_in_data)

        self._expected_attachment_out = AttachmentOut(**self._attachment_in.model_dump())

        RepositoryTestHelpers.mock_insert_one(self.attachments_collection, self._attachment_in.id)
        RepositoryTestHelpers.mock_find_one(
            self.attachments_collection, {**self._attachment_in.model_dump(), "_id": self._attachment_in.id}
        )

    def call_create(self) -> None:
        """Calls the `AttachmentRepo` `create` method with the appropriate data from a prior call to `mock_create`."""

        self._created_attachment = self.attachment_repository.create(self._attachment_in, session=self.mock_session)

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.attachments_collection.insert_one.assert_called_once_with(
            self._attachment_in.model_dump(by_alias=True), session=self.mock_session
        )
        self.attachments_collection.find_one.assert_called_once_with(
            {"_id": self._attachment_in.id}, session=self.mock_session
        )

        assert self._created_attachment == self._expected_attachment_out


class TestCreate(CreateDSL):
    """Tests for creating an attachment."""

    def test_create(self):
        """Test creating an attachment."""

        self.mock_create(ATTACHMENT_IN_DATA_ALL_VALUES)
        self.call_create()
        self.check_create_success()
