"""
Unit tests for the `AttachmentService` service.
"""

from test.mock_data import (
    ATTACHMENT_IN_DATA_ALL_VALUES,
    ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES,
    ATTACHMENT_POST_DATA_ALL_VALUES,
)
from typing import List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from bson import ObjectId

from object_storage_api.core.config import config
from object_storage_api.core.exceptions import FileTypeMismatchException, InvalidObjectIdError, UploadLimitReachedError
from object_storage_api.models.attachment import AttachmentIn, AttachmentOut
from object_storage_api.schemas.attachment import (
    AttachmentMetadataSchema,
    AttachmentPatchMetadataSchema,
    AttachmentPostResponseSchema,
    AttachmentPostSchema,
    AttachmentPostUploadInfoSchema,
    AttachmentSchema,
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

    def mock_create(self, attachment_post_data: dict, attachment_count: int) -> None:
        """
        Mocks repo & store methods appropriately to test the `create` service method.

        :param attachment_post_data: Dictionary containing the basic attachment data as would be required for a
            `AttachmentPostSchema` (i.e. no created and modified times required).
        :param attachment_count: The number of attachments currently stored in the database.
        """

        self._attachment_post = AttachmentPostSchema(**attachment_post_data)

        self._expected_attachment_id = ObjectId()
        self.mock_object_id.return_value = self._expected_attachment_id

        self.mock_attachment_repository.count_by_entity_id.return_value = attachment_count

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
        `mock_create` while expecting an error to be raised.

        :param error_type: Expected exception to be raised.
        """

        with pytest.raises(error_type) as exc:
            self.attachment_service.create(self._attachment_post)
        self._create_exception = exc

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.mock_attachment_repository.count_by_entity_id.assert_called_once_with(
            str(self._expected_attachment_in.entity_id)
        )

        self.mock_attachment_store.create_presigned_post.assert_called_once_with(
            str(self._expected_attachment_id), self._attachment_post
        )
        self.mock_attachment_repository.create.assert_called_once_with(self._expected_attachment_in)

        assert self._created_attachment == self._expected_attachment

    def check_create_failed_with_exception(self, message: str, assert_count: bool = True) -> None:
        """
        Checks that a prior call to `call_create_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        :param assert_count: Whether the `count_by_entity_id` repo method is expected to be called or not.
        """
        if assert_count:
            self.mock_attachment_repository.count_by_entity_id.assert_called_once_with(
                str(self._expected_attachment_in.entity_id)
            )
        else:
            self.mock_attachment_repository.count_by_entity_id.assert_not_called()

        self.mock_attachment_store.create_presigned_post.assert_not_called()
        self.mock_attachment_repository.create.assert_not_called()

        assert str(self._create_exception.value) == message


class TestCreate(CreateDSL):
    """Tests for creating an attachment."""

    def test_create(self):
        """Test creating an attachment."""

        self.mock_create(ATTACHMENT_POST_DATA_ALL_VALUES, 0)
        self.call_create()
        self.check_create_success()

    def test_create_with_invalid_entity_id(self):
        """Test creating an attachment with an invalid `entity_id`."""

        self.mock_create({**ATTACHMENT_POST_DATA_ALL_VALUES, "entity_id": "invalid-id"}, 0)
        self.call_create_expecting_error(InvalidObjectIdError)
        self.check_create_failed_with_exception("Invalid ObjectId value 'invalid-id'", False)

    def test_create_when_upload_limit_reached(self):
        """Test creating an attachment when the upload limit has been reached."""

        self.mock_create(ATTACHMENT_POST_DATA_ALL_VALUES, config.attachment.upload_limit)
        self.call_create_expecting_error(UploadLimitReachedError)
        self.check_create_failed_with_exception(
            "Unable to create an attachment as the upload limit for attachments with `entity_id` "
            f"'{ATTACHMENT_POST_DATA_ALL_VALUES["entity_id"]}' has been reached",
            True,
        )


class GetDSL(AttachmentServiceDSL):
    """Base class for `get` tests."""

    _obtained_attachment_id: str
    _expected_attachment_out: AttachmentOut
    _expected_attachment: AttachmentSchema
    _obtained_attachment: AttachmentSchema

    def mock_get(self) -> None:
        """Mocks repo methods appropriately to test the `get` service method."""

        self._expected_attachment_out = AttachmentOut(**AttachmentIn(**ATTACHMENT_IN_DATA_ALL_VALUES).model_dump())
        self.mock_attachment_repository.get.return_value = self._expected_attachment_out
        self.mock_attachment_store.create_presigned_get.return_value = "https://fakepresignedurl.co.uk/attachment"
        self._expected_attachment = AttachmentSchema(
            **self._expected_attachment_out.model_dump(), download_url="https://fakepresignedurl.co.uk/attachment"
        )

    def call_get(self, attachment_id: str) -> None:
        """
        Calls the `AttachmentService` `get` method.

        :param attachment_id: The ID of the attachment to obtain.
        """
        self._obtained_attachment_id = attachment_id
        self._obtained_attachment = self.attachment_service.get(attachment_id=attachment_id)

    def check_get_success(self) -> None:
        """Checks that a prior call to `call_get` worked as expected."""
        self.mock_attachment_repository.get.assert_called_once_with(attachment_id=self._obtained_attachment_id)
        self.mock_attachment_store.create_presigned_get.assert_called_once_with(self._expected_attachment_out)
        assert self._obtained_attachment == self._expected_attachment


class TestGet(GetDSL):
    """Tests for getting attachments."""

    def test_get(self):
        """Test getting attachments."""
        self.mock_get()
        self.call_get(str(ObjectId()))
        self.check_get_success()


class ListDSL(AttachmentServiceDSL):
    """Base class for `list` tests."""

    _entity_id_filter: Optional[str]
    _expected_attachments: List[AttachmentMetadataSchema]
    _obtained_attachments: List[AttachmentMetadataSchema]

    def mock_list(self) -> None:
        """Mocks repo methods appropriately to test the `list` service method."""

        # Just returns the result after converting it to the schemas currently, so actual value doesn't matter here.
        attachments_out = [AttachmentOut(**AttachmentIn(**ATTACHMENT_IN_DATA_ALL_VALUES).model_dump())]
        self.mock_attachment_repository.list.return_value = attachments_out
        self._expected_attachments = [
            AttachmentMetadataSchema(**attachment_out.model_dump()) for attachment_out in attachments_out
        ]

    def call_list(self, entity_id: Optional[str] = None) -> None:
        """
        Calls the `AttachmentService` `list` method.

        :param entity_id: The ID of the entity to filter attachments by.
        """
        self._entity_id_filter = entity_id
        self._obtained_attachments = self.attachment_service.list(entity_id=entity_id)

    def check_list_success(self) -> None:
        """Checks that a prior call to `call_list` worked as expected."""
        self.mock_attachment_repository.list.assert_called_once_with(self._entity_id_filter)
        assert self._obtained_attachments == self._expected_attachments


class TestList(ListDSL):
    """Tests for listing attachments."""

    def test_list(self):
        """Test listing attachments."""
        self.mock_list()
        self.call_list(entity_id=str(ObjectId()))
        self.check_list_success()


class UpdateDSL(AttachmentServiceDSL):
    """Base class for `update` tests."""

    _stored_attachment: Optional[AttachmentOut]
    _attachment_patch: AttachmentPatchMetadataSchema
    _expected_attachment_in: AttachmentIn
    _expected_attachment_out: AttachmentOut
    _updated_attachment_id: str
    _updated_attachment: MagicMock
    _update_exception: pytest.ExceptionInfo

    def mock_update(self, attachment_patch_data: dict, stored_attachment_post_data: Optional[dict]) -> None:
        """
        Mocks the repository methods appropriately to test the `update` service method.

        :param attachment_patch_data: Dictionary containing the patch data as would be required for an
            `AttachmentPatchMetadataSchema` (i.e. no created or modified times required).
        :param stored_attachment_post_data: Dictionary containing the attachment data for the existing stored
            attachment as would be required for an `AttachmentPostMetadataSchema` (i.e. no created and modified
            times required).
        """

        # Stored attachment
        self._stored_attachment = (
            AttachmentOut(
                **AttachmentIn(
                    **stored_attachment_post_data,
                ).model_dump(),
            )
            if stored_attachment_post_data
            else None
        )
        self.mock_attachment_repository.get.return_value = self._stored_attachment

        # Patch schema
        self._attachment_patch = AttachmentPatchMetadataSchema(**attachment_patch_data)

        # Construct the expected input for the repository
        merged_attachment_data = {**(stored_attachment_post_data or {}), **attachment_patch_data}
        self._expected_attachment_in = AttachmentIn(**merged_attachment_data)

        # Updated attachment
        attachment_out = AttachmentOut(
            **self._expected_attachment_in.model_dump(),
        )

        self.mock_attachment_repository.update.return_value = attachment_out

        self._expected_attachment_out = AttachmentMetadataSchema(**attachment_out.model_dump())

    def call_update(self, attachment_id: str) -> None:
        """
        Class the `AttachmentService` `update` method with the appropriate data from a prior call to `mock_update`.

        :param attachment_id: ID of the attachment to be updated.
        """

        self._updated_attachment_id = attachment_id
        self._updated_attachment = self.attachment_service.update(attachment_id, self._attachment_patch)

    def call_update_expecting_error(self, attachment_id: str, error_type: type[BaseException]) -> None:
        """
        Class the `AttachmentService` `update` method with the appropriate data from a prior call to `mock_update`,
        while expecting an error to be raised.

        :param attachment_id: ID of the attachment to be updated.
        :param error_type: Expected exception to be raised.
        """

        self._updated_attachment_id = attachment_id
        with pytest.raises(error_type) as exc:
            self.attachment_service.update(attachment_id, self._attachment_patch)
        self._update_exception = exc

    def check_update_success(self) -> None:
        """Checks that a prior call to `call_update` worked as expected."""

        # Ensure obtained old attachment
        self.mock_attachment_repository.get.assert_called_once_with(attachment_id=self._updated_attachment_id)

        # Ensure updated with expected data
        self.mock_attachment_repository.update.assert_called_once_with(
            attachment_id=self._updated_attachment_id,
            attachment=self._expected_attachment_in,
        )

        assert self._updated_attachment == self._expected_attachment_out

    def check_update_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_update_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        """

        self.mock_attachment_repository.get.assert_called_once_with(attachment_id=self._updated_attachment_id)
        self.mock_attachment_repository.update.assert_not_called()

        assert str(self._update_exception.value) == message


class TestUpdate(UpdateDSL):
    """Tests for updating an attachment."""

    def test_update(self):
        """Test updating all fields of an attachment."""
        attachment_id = str(ObjectId())

        self.mock_update(
            attachment_patch_data=ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES,
            stored_attachment_post_data=ATTACHMENT_IN_DATA_ALL_VALUES,
        )

        self.call_update(attachment_id)
        self.check_update_success()

    def test_update_with_file_extension_content_type_mismatch(self):
        """Test updating filename to one with a mismatched file extension."""
        attachment_id = str(ObjectId())

        self.mock_update(
            attachment_patch_data={**ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES, "file_name": "report.mp3"},
            stored_attachment_post_data=ATTACHMENT_IN_DATA_ALL_VALUES,
        )

        self.call_update_expecting_error(attachment_id, FileTypeMismatchException)
        self.check_update_failed_with_exception(
            f"Patch filename extension of '{self._attachment_patch.file_name}' does not match "
            f"that of the stored attachment '{self._stored_attachment.file_name}'"
        )


class DeleteDSL(AttachmentServiceDSL):
    """Base class for `delete` tests."""

    _expected_attachment_out: AttachmentOut
    _delete_attachment_id: str
    _delete_attachment_object_key: str

    def mock_delete(self, attachment_in_data: dict) -> None:
        """
        Mocks repo methods appropriately to test the `delete` service method.
        :param attachment_in_data: Dictionary containing the attachment data as would be required for an `AttachmentIn`
            database model (i.e. no created and modified times required).
        """
        self._expected_attachment_out = AttachmentOut(**AttachmentIn(**attachment_in_data).model_dump())
        self.mock_attachment_repository.get.return_value = self._expected_attachment_out
        self._delete_attachment_id = self._expected_attachment_out.id
        self._delete_attachment_object_key = self._expected_attachment_out.object_key

    def call_delete(self) -> None:
        """Calls the `AttachmentService` `delete` method."""
        self.attachment_service.delete(self._delete_attachment_id)

    def check_delete_success(self) -> None:
        """Checks that a prior call to `call_delete` worked as expected."""
        self.mock_attachment_store.delete.assert_called_once_with(self._delete_attachment_object_key)
        self.mock_attachment_repository.delete.assert_called_once_with(self._delete_attachment_id)


class TestDelete(DeleteDSL):
    """Tests for deleting an attachment."""

    def test_delete(self):
        """Test for deleting an attachment."""
        self.mock_delete(ATTACHMENT_IN_DATA_ALL_VALUES)
        self.call_delete()
        self.check_delete_success()


class DeleteByEntityIdDSL(AttachmentServiceDSL):
    """Base class for `delete_by_entity_id` tests."""

    _expected_attachments_out: list[AttachmentOut]
    _delete_entity_id: str
    _delete_attachment_object_keys: list[str]

    def mock_delete_by_entity_id(self, attachments_in_data: list[dict]) -> None:
        """
        Mocks repo methods appropriately to test the `delete_by_entity_id` service method.

        :param attachments_in_data: List of dictionaries containing the attachment data as would be required for an
            `AttachmentIn` database model (i.e. no created and modified times required).
        """
        self._expected_attachments_out = [
            AttachmentOut(**AttachmentIn(**attachment_in_data).model_dump())
            for attachment_in_data in attachments_in_data
        ]
        self.mock_attachment_repository.list.return_value = self._expected_attachments_out
        self._delete_entity_id = (
            self._expected_attachments_out[0].id if self._expected_attachments_out else str(ObjectId())
        )
        self._delete_attachment_object_keys = [
            expected_attachment_out.object_key for expected_attachment_out in self._expected_attachments_out
        ]

    def call_delete_by_entity_id(self) -> None:
        """Calls the `AttachmentService` `delete_by_entity_id` method."""
        self.attachment_service.delete_by_entity_id(self._delete_entity_id)

    def check_delete_by_entity_id_success(self, assert_delete: bool = True) -> None:
        """
        Checks that a prior call to `call_delete_by_entity_id` worked as expected.

        :param assert_delete: Whether the `delete_many` store method and `delete_by_entity_id` repo method are expected
            to be called or not.
        """
        if assert_delete:
            self.mock_attachment_store.delete_many.assert_called_once_with(self._delete_attachment_object_keys)
            self.mock_attachment_repository.delete_by_entity_id.assert_called_once_with(self._delete_entity_id)
        else:
            self.mock_attachment_store.delete_many.assert_not_called()
            self.mock_attachment_repository.delete_by_entity_id.assert_not_called()


# Expect some duplicate code inside tests as the tests for the different entities can be very similar
# pylint: disable=duplicate-code


class TestDeleteByEntityId(DeleteByEntityIdDSL):
    """Tests for deleting attachments by `entity_id`."""

    def test_delete_by_entity_id(self):
        """Test deleting attachments."""
        self.mock_delete_by_entity_id([ATTACHMENT_IN_DATA_ALL_VALUES])
        self.call_delete_by_entity_id()
        self.check_delete_by_entity_id_success()

    def test_delete_by_entity_id_non_existent_id(self):
        """Test deleting attachments with a non-existent `entity_id`."""
        self.mock_delete_by_entity_id([])
        self.call_delete_by_entity_id()
        self.check_delete_by_entity_id_success(False)


# pylint: enable=duplicate-code
