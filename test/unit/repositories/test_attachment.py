"""
Unit tests for the `AttachmentRepo` repository.
"""

from test.mock_data import ATTACHMENT_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from typing import Optional
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId

from object_storage_api.core.exceptions import InvalidObjectIdError, MissingRecordError
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


class GetDSL(AttachmentRepoDSL):
    """Base class for `get` tests."""

    _obtained_attachment_id: str
    _expected_attachment_out: AttachmentOut
    _obtained_attachment_out: AttachmentOut
    _get_exception: pytest.ExceptionInfo

    def mock_get(self, attachment_id: str, attachment_in_data: Optional[dict] = None) -> None:
        """
        Mocks database methods appropriately to test the `get` repo method.

        :param attachment_id: ID of the attachment to obtain.
        :param attachment_in_data: Dictionary containing the attachment data as would be required for an
            `AttachmentIn` database model (i.e. no created and modified times required).
        """
        if attachment_in_data:
            attachment_in_data["id"] = attachment_id
        self._expected_attachment_out = (
            AttachmentOut(**AttachmentIn(**attachment_in_data).model_dump()) if attachment_in_data else None
        )

        RepositoryTestHelpers.mock_find_one(
            self.attachments_collection,
            self._expected_attachment_out.model_dump() if self._expected_attachment_out else None,
        )

    def call_get(self, attachment_id: str) -> None:
        """
        Calls the `AttachmentRepo` `get` method.

        :param attachment_id: The ID of the attachment to obtain.
        """
        self._obtained_attachment_id = attachment_id
        self._obtained_attachment_out = self.attachment_repository.get(
            attachment_id=attachment_id, session=self.mock_session
        )

    def call_get_expecting_error(self, attachment_id: str, error_type: type[BaseException]) -> None:
        """
        Calls the `AttachmentRepo` `get` method with the appropriate data from a prior call to `mock_get`
        while expecting an error to be raised.

        :param attachment_id: ID of the attachment to be obtained.
        :param error_type: Expected exception to be raised.
        """
        self._obtained_attachment_id = attachment_id
        with pytest.raises(error_type) as exc:
            self.attachment_repository.get(attachment_id, session=self.mock_session)
        self._get_exception = exc

    def check_get_success(self) -> None:
        """Checks that a prior call to `call_get` worked as expected."""

        self.attachments_collection.find_one.assert_called_once_with(
            {"_id": ObjectId(self._obtained_attachment_id)}, session=self.mock_session
        )
        assert self._obtained_attachment_out == self._expected_attachment_out

    def check_get_failed_with_exception(self, message: str, assert_find: bool = False) -> None:
        """
        Checks that a prior call to `call_get_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Expected message of the raised exception.
        :param assert_find: If `True` it asserts whether a `find_one` call was made,
            else it asserts that no call was made.
        """
        if assert_find:
            self.attachments_collection.find_one.assert_called_once_with(
                {"_id": ObjectId(self._obtained_attachment_id)}, session=self.mock_session
            )
        else:
            self.attachments_collection.find_one.assert_not_called()

        assert str(self._get_exception.value) == message


class TestGet(GetDSL):
    """Tests for getting attachments."""

    def test_get(self):
        """Test getting an attachment."""

        attachment_id = str(ObjectId())

        self.mock_get(attachment_id, ATTACHMENT_IN_DATA_ALL_VALUES)
        self.call_get(attachment_id)
        self.check_get_success()

    def test_get_with_non_existent_id(self):
        """Test getting an attachment with a non-existent attachment ID."""

        attachment_id = str(ObjectId())

        self.mock_get(attachment_id)
        self.call_get_expecting_error(attachment_id, MissingRecordError)
        self.check_get_failed_with_exception(f"No attachment found with ID: {attachment_id}", True)

    def test_get_with_invalid_id(self):
        """Test getting an attachment with an invalid attachment ID."""
        attachment_id = "invalid-id"

        self.mock_get(attachment_id)
        self.call_get_expecting_error(attachment_id, InvalidObjectIdError)
        self.check_get_failed_with_exception(f"Invalid ObjectId value '{attachment_id}'")


class ListDSL(AttachmentRepoDSL):
    """Base class for `list` tests."""

    _expected_attachment_out: list[AttachmentOut]
    _entity_id_filter: Optional[str]
    _obtained_attachment_out: list[AttachmentOut]

    def mock_list(self, attachment_in_data: list[dict]) -> None:
        """
        Mocks database methods appropriately to test the `list` repo method.

        :param attachment_in_data: List of dictionaries containing the attachment data as would be required for an
            `AttachmentIn` database model (i.e. no created and modified times required).
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
        Calls the `AttachmentRepo` `list` method.

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

    def check_list_returned_an_empty_list(self) -> None:
        """Checks that a prior call to `call_list` with an invalid entity_id returned an empty list as expected."""

        self.attachments_collection.find.assert_not_called()

        assert self._obtained_attachment_out == []


# Expect some duplicate code inside tests as the tests for the different entities can be very similar
# pylint: disable=duplicate-code


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

    def test_list_with_entity_id_with_no_results(self):
        """Test listing all attachments with an `entity_id` argument returning no results."""

        entity_id = str(ObjectId())

        self.mock_list([])
        self.call_list(entity_id)
        self.check_list_success()

    def test_list_with_invalid_id_returns_empty_list(self):
        """Test listing all attachments with an invalid `entity_id` argument returns an empty list."""

        entity_id = "invalid-id"

        self.mock_list([ATTACHMENT_IN_DATA_ALL_VALUES])
        self.call_list(entity_id)
        self.check_list_returned_an_empty_list()


class DeleteDSL(AttachmentRepoDSL):
    """Base class for `delete` tests."""

    _delete_attachment_id: str
    _delete_exception: pytest.ExceptionInfo

    def mock_delete(self, deleted_count: int) -> None:
        """
        Mocks database methods appropriately to test the `delete` repo method.
        :param deleted_count: Number of documents deleted successfully.
        """
        RepositoryTestHelpers.mock_delete_one(self.attachments_collection, deleted_count)

    def call_delete(self, attachment_id: str) -> None:
        """
        Calls the `AttachmentRepo` `delete` method.
        :param attachment_id: ID of the attachment to be deleted.
        """
        self._delete_attachment_id = attachment_id
        self.attachment_repository.delete(attachment_id, session=self.mock_session)

    def call_delete_expecting_error(self, attachment_id: str, error_type: type[BaseException]) -> None:
        """
        Calls the `AttachmentRepo` `delete` method while expecting an error to be raised.
        :param attachment_id: ID of the attachment to be deleted.
        :param error_type: Expected exception to be raised.
        """
        self._delete_attachment_id = attachment_id
        with pytest.raises(error_type) as exc:
            self.attachment_repository.delete(attachment_id, session=self.mock_session)
        self._delete_exception = exc

    def check_delete_success(self) -> None:
        """Checks that a prior call to `call_delete` worked as expected."""
        self.attachments_collection.delete_one.assert_called_once_with(
            filter={"_id": ObjectId(self._delete_attachment_id)}, session=self.mock_session
        )

    def check_delete_failed_with_exception(self, message: str, assert_delete: bool = False) -> None:
        """
        Checks that a prior call to `call_delete_expecting_error` worked as expected, raising an exception
        with the correct message.
        :param message: Expected message of the raised exception.
        :param assert_delete: Whether the `find_one_and_delete` method is expected to be called or not.
        """
        if not assert_delete:
            self.attachments_collection.delete_one.assert_not_called()
        else:
            self.attachments_collection.delete_one.assert_called_once_with(
                filter={"_id": ObjectId(self._delete_attachment_id)},
                session=self.mock_session,
            )

        assert str(self._delete_exception.value) == message


class TestDelete(DeleteDSL):
    """Tests for deleting an attachment."""

    def test_delete(self):
        """Test deleting an attachment."""
        self.mock_delete(1)
        self.call_delete(str(ObjectId()))
        self.check_delete_success()

    def test_delete_non_existent_id(self):
        """Test deleting an attachment with a non-existent ID."""
        attachment_id = str(ObjectId())

        self.mock_delete(0)
        self.call_delete_expecting_error(attachment_id, MissingRecordError)
        self.check_delete_failed_with_exception(f"No attachment found with ID: {attachment_id}", assert_delete=True)

    def test_delete_invalid_id(self):
        """Test deleting an attachment with an invalid ID."""
        attachment_id = "invalid-id"

        self.call_delete_expecting_error(attachment_id, InvalidObjectIdError)
        self.check_delete_failed_with_exception(f"Invalid ObjectId value '{attachment_id}'")


# pylint: enable=duplicate-code


class DeleteByEntityIdDSL(AttachmentRepoDSL):
    """Base class for `delete_by_entity_id` tests."""

    _delete_entity_id: str
    _delete_by_entity_id_exception: pytest.ExceptionInfo

    def mock_delete_by_entity_id(self, deleted_count: int) -> None:
        """
        Mocks database methods appropriately to test the `delete_by_entity_id` repo method.

        :param deleted_count: Number of documents deleted successfully.
        """
        RepositoryTestHelpers.mock_delete_many(self.attachments_collection, deleted_count)

    def call_delete_by_entity_id(self, entity_id: str) -> None:
        """
        Calls the `AttachmentRepo` `delete_by_entity_id` method.

        :param entity_id: The entity ID of the attachments to be deleted.
        """
        self._delete_entity_id = entity_id
        self.attachment_repository.delete_by_entity_id(entity_id, session=self.mock_session)

    def check_delete_by_entity_id_success(self, assert_delete: bool = True) -> None:
        """
        Checks that a prior call to `call_delete_by_entity_id` worked as expected.

        :param assert_delete: Whether the `delete_many` method is expected to be called or not.
        """
        if assert_delete:
            self.attachments_collection.delete_many.assert_called_once_with(
                filter={"entity_id": ObjectId(self._delete_entity_id)}, session=self.mock_session
            )
        else:
            self.attachments_collection.delete_many.assert_not_called()


class TestDeleteByEntityId(DeleteByEntityIdDSL):
    """Tests for deleting attachments by entity ID."""

    def test_delete_by_entity_id(self):
        """Test deleting attachments."""
        self.mock_delete_by_entity_id(3)
        self.call_delete_by_entity_id(str(ObjectId()))
        self.check_delete_by_entity_id_success()

    def test_delete_by_entity_id_invalid_id(self):
        """Test deleting attachments with an invalid entity ID."""
        entity_id = "invalid-id"

        self.call_delete_by_entity_id(entity_id)
        self.check_delete_by_entity_id_success(False)


class UpdateDSL(AttachmentRepoDSL):
    """Base class for `update` tests."""

    _attachment_in: AttachmentIn
    _expected_attachment_out: AttachmentOut
    _updated_attachment_id: str
    _updated_attachment: AttachmentOut
    _update_exception: pytest.ExceptionInfo

    def set_update_data(self, new_attachment_in_data: dict):
        """
        Assigns the update data to use during a call to `call_update`.

        :param new_attachment_in_data: New attachment data as would be required for an `AttachmentIn` database model
            to supply to the `AttachmentRepo` `update` method.
        """

        self._attachment_in = AttachmentIn(**new_attachment_in_data)

    def mock_update(self, new_attachment_in_data: dict) -> None:
        """Mocks database methods appropriately to test the `update` repo method.

        :param new_attachment_in_data: Dictionary containing the new attachment data as would be required for an
            `Attachment_In` database model (i.e. no created and modified times required).
        """

        self.set_update_data(new_attachment_in_data)

        self._expected_attachment_out = AttachmentOut(**self._attachment_in.model_dump())
        RepositoryTestHelpers.mock_find_one(
            self.attachments_collection,
            self._expected_attachment_out.model_dump(by_alias=True),
        )

    def call_update(self, attachment_id: str) -> None:
        """
        Calls the `AttachmentRepo` `update` method with the appropriate data from a prior call to `mock_update`
        (or `set_update_data`).

        :param attachment_id: ID of the attachment to be updated.
        """

        self._updated_attachment_id = attachment_id
        self._updated_attachment = self.attachment_repository.update(
            attachment_id,
            self._attachment_in,
            session=self.mock_session,
        )

    def call_update_expecting_error(self, attachment_id: str, error_type: type[BaseException]) -> None:
        """
        Calls the `AttachmentRepo `update` method with the appropriate data from a prior call to `mock_update`
        (or `set_update_data`) while expecting an error to be raised.

        :param attachment_id: ID of the attachment to be updated.
        :param error_type: Expected exception to be raised.
        """

        with pytest.raises(error_type) as exc:
            self.attachment_repository.update(attachment_id, self._attachment_in)
        self._update_exception = exc

    def check_update_success(self) -> None:
        """Checks that a prior call to `call_update` worked as expected."""

        self.attachments_collection.update_one.assert_called_once_with(
            {
                "_id": ObjectId(self._updated_attachment_id),
            },
            {
                "$set": self._attachment_in.model_dump(by_alias=True),
            },
            session=self.mock_session,
        )

        assert self._updated_attachment == self._expected_attachment_out

    def check_update_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_update_expecting_error` failed as expected, raising an exception
        with the correct message.

        :param message: Expected message of the raised exception.
        """

        self.attachments_collection.update_one.assert_not_called()

        assert str(self._update_exception.value) == message


class TestUpdate(UpdateDSL):
    """Tests for updating an attachment."""

    def test_update(self):
        """Test updating an attachment."""

        attachment_id = str(ObjectId())

        self.mock_update(ATTACHMENT_IN_DATA_ALL_VALUES)
        self.call_update(attachment_id)
        self.check_update_success()

    def test_update_with_invalid_id(self):
        """Test updating an attachment with an invalid ID."""

        attachment_id = "invalid-id"

        self.set_update_data(ATTACHMENT_IN_DATA_ALL_VALUES)
        self.call_update_expecting_error(attachment_id, InvalidObjectIdError)
        self.check_update_failed_with_exception("Invalid ObjectId value 'invalid-id'")
