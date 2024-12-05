"""
Unit tests for the `AttachmentRepo` repository.
"""

from test.mock_data import ATTACHMENT_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from typing import Optional
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId

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


class ListDSL(AttachmentRepoDSL):
    """Base class for `list` tests."""

    _expected_attachment_out: list[AttachmentOut]
    _entity_id_filter: Optional[str]
    _obtained_attachment_out: list[AttachmentOut]

    def mock_list(self, attachment_in_data: list[dict]) -> None:
        """
        Mocks database methods appropriately to test the `list` repo method.

        :param attachment_in_data: List of dictionaries containing the attachment data as would be required for an
            `AttachmentIn` database model (i.e. no ID or created and modified times required).
        """
        self._expected_attachment_out = [
            AttachmentOut(**AttachmentIn(**attachment_in_data).model_dump())
            for attachment_in_data in attachment_in_data
        ]

        RepositoryTestHelpers.mock_find(
            self.attachments_collection,
            [attachment_out.model_dump() for attachment_out in self._expected_attachment_out],
        )

    def call_list(self, entity_id: Optional[str] = None) -> None:
        """
        Calls the `AttachmentRepo` `list method` method.

        :param entity_id: The ID of the entity to filter attachments by.
        """
        self._entity_id_filter = entity_id
        self._obtained_attachment_out = self.attachment_repository.list(session=self.mock_session, entity_id=entity_id)

    def check_list_success(self) -> None:
        """Checks that a prior call to `call_list` worked as expected."""
        expected_query = {}
        if self._entity_id_filter is not None:
            expected_query["entity_id"] = ObjectId(self._entity_id_filter)

        self.attachments_collection.find.assert_called_once_with(expected_query, session=self.mock_session)
        assert self._obtained_attachment_out == self._expected_attachment_out


class TestList(ListDSL):
    """Tests for listing attachments."""

    def test_list(self):
        """Test listing all attachments."""
        self.mock_list([ATTACHMENT_IN_DATA_ALL_VALUES])
        self.call_list()
        self.check_list_success()

    def test_list_with_no_results(self):
        """Test listing all attachments returning no results."""
        self.mock_list([])
        self.call_list()
        self.check_list_success()

    def test_list_with_entity_id(self):
        """Test listing all attachments with an `entity_id` argument."""
        self.mock_list([ATTACHMENT_IN_DATA_ALL_VALUES])
        self.call_list(entity_id=ATTACHMENT_IN_DATA_ALL_VALUES["entity_id"])
        self.check_list_success()
