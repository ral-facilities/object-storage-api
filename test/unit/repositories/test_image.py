"""
Unit tests for the `ImageRepo` repository.
"""

from test.mock_data import IMAGE_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from typing import Optional
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId

from object_storage_api.core.exceptions import MissingRecordError
from object_storage_api.models.image import ImageIn, ImageOut
from object_storage_api.repositories.image import ImageRepo


class ImageRepoDSL:
    """Base class for `ImageRepo` unit tests."""

    mock_database: Mock
    image_repository: ImageRepo
    images_collection: Mock

    mock_session = MagicMock()

    @pytest.fixture(autouse=True)
    def setup(self, database_mock):
        """Setup fixtures"""

        self.mock_database = database_mock
        self.image_repository = ImageRepo(database_mock)
        self.images_collection = database_mock.images


class CreateDSL(ImageRepoDSL):
    """Base class for `create` tests."""

    _image_in: ImageIn
    _expected_image_out: ImageOut
    _created_image: ImageOut
    _create_exception: pytest.ExceptionInfo

    def mock_create(
        self,
        image_in_data: dict,
    ) -> None:
        """
        Mocks database methods appropriately to test the `create` repo method.

        :param image_in_data: Dictionary containing the image data as would be required for a `ImageIn`
                                   database model (i.e. no created and modified times required).
        """

        # Pass through `ImageIn` first as need creation and modified times
        self._image_in = ImageIn(**image_in_data)

        self._expected_image_out = ImageOut(**self._image_in.model_dump())

        RepositoryTestHelpers.mock_insert_one(self.images_collection, self._image_in.id)
        RepositoryTestHelpers.mock_find_one(
            self.images_collection, {**self._image_in.model_dump(), "_id": self._image_in.id}
        )

    def call_create(self) -> None:
        """Calls the `ImageRepo` `create` method with the appropriate data from a prior call to `mock_create`."""

        self._created_image = self.image_repository.create(self._image_in, session=self.mock_session)

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.images_collection.insert_one.assert_called_once_with(
            self._image_in.model_dump(by_alias=True), session=self.mock_session
        )
        self.images_collection.find_one.assert_called_once_with({"_id": self._image_in.id}, session=self.mock_session)

        assert self._created_image == self._expected_image_out


class TestCreate(CreateDSL):
    """Tests for creating an image."""

    def test_create(self):
        """Test creating an image."""

        self.mock_create(IMAGE_IN_DATA_ALL_VALUES)
        self.call_create()
        self.check_create_success()


class ListDSL(ImageRepoDSL):
    """Base class for `list` tests."""

    _expected_image_out: list[ImageOut]
    _entity_id_filter: Optional[str]
    _primary_filter: Optional[bool]
    _obtained_image_out: list[ImageOut]

    def mock_list(self, image_in_data: list[dict]) -> None:
        """
        Mocks database methods appropriately to test the `list` repo method.

        :param image_in_data: List of dictionaries containing the image data as would be required for an
            `ImageIn` database model (i.e. no ID or created and modified times required).
        """
        self._expected_image_out = [
            ImageOut(**ImageIn(**image_in_data).model_dump()) for image_in_data in image_in_data
        ]

        RepositoryTestHelpers.mock_find(
            self.images_collection, [image_out.model_dump() for image_out in self._expected_image_out]
        )

    def call_list(self, entity_id: Optional[str] = None, primary: Optional[bool] = None) -> None:
        """Calls the `ImageRepo` `list method` method.

        :param entity_id: The ID of the entity to filter images by.
        :param primary: The primary value to filter images by.
        """
        self._entity_id_filter = entity_id
        self._primary_filter = primary
        self._obtained_image_out = self.image_repository.list(
            session=self.mock_session, entity_id=entity_id, primary=primary
        )

    def check_list_success(self) -> None:
        """Checks that a prior call to `call_list` worked as expected."""
        expected_query = {}
        if self._entity_id_filter is not None:
            expected_query["entity_id"] = ObjectId(self._entity_id_filter)
        if self._primary_filter is not None:
            expected_query["primary"] = self._primary_filter

        self.images_collection.find.assert_called_once_with(expected_query, session=self.mock_session)
        assert self._obtained_image_out == self._expected_image_out


class TestList(ListDSL):
    """Tests for listing images."""

    def test_list(self):
        """Test listing all images."""
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES])
        self.call_list()
        self.check_list_success()

    def test_list_with_no_results(self):
        """Test listing all images returning no results."""
        self.mock_list([])
        self.call_list()
        self.check_list_success()

    def test_list_with_entity_id(self):
        """Test listing all images with an `entity_id` argument."""
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES])
        self.call_list(entity_id=IMAGE_IN_DATA_ALL_VALUES["entity_id"])
        self.check_list_success()

    def test_list_with_primary(self):
        """Test listing all images with a `primary` argument."""
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES])
        self.call_list(primary=False)
        self.check_list_success()

    def test_list_with_primary_and_entity_id(self):
        """Test listing all images with an `entity_id` and `primary` argument."""
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES])
        self.call_list(primary=True, entity_id=IMAGE_IN_DATA_ALL_VALUES["entity_id"])
        self.check_list_success()


class DeleteDSL(ImageRepoDSL):
    """Base class for `delete` tests."""

    _delete_image_id: str
    _delete_exception: pytest.ExceptionInfo
    _expected_image_out: ImageOut
    _obtained_image_out: ImageOut
    _expected_object_key: str
    _obtained_object_key: str

    def mock_delete(self, image_id: str, image_in_data: dict = None) -> None:
        """
        Mocks database methods appropriately to test the `delete` repo method.

        :param deleted_count: Number of documents deleted successfully.
        """
        if image_in_data:
            image_in_data["id"] = image_id
        self._expected_image_out = ImageOut(**ImageIn(**image_in_data).model_dump()) if image_in_data else None
        RepositoryTestHelpers.mock_find_one_and_delete(
            self.images_collection, self._expected_image_out.model_dump() if image_in_data else None
        )
        if self._expected_image_out:
            self._expected_object_key = self._expected_image_out.object_key

    def call_delete(self, image_id: str) -> None:
        """
        Calls the `ImageRepo` `delete` method.

        :param image_id: ID of the image to be deleted.
        """

        self._delete_image_id = image_id
        self._obtained_object_key = self.image_repository.delete(image_id, session=self.mock_session)

    def call_delete_expecting_error(self, image_id: str, error_type: type[BaseException]) -> None:
        """
        Calls the `ImageRepo` `delete` method while expecting an error to be raised.

        :param image_id: ID of the image to be deleted.
        :param error_type: Expected exception to be raised.
        """

        self._delete_image_id = image_id
        with pytest.raises(error_type) as exc:
            self.image_repository.delete(image_id, session=self.mock_session)
        self._delete_exception = exc

    def check_delete_success(self) -> None:
        """Checks that a prior call to `call_delete` worked as expected."""

        self.images_collection.find_one_and_delete.assert_called_once_with(
            filter={"_id": ObjectId(self._delete_image_id)}, projection={"object_key": True}, session=self.mock_session
        )
        self._obtained_object_key = self._expected_object_key

    def check_delete_failed_with_exception(self, message: str, assert_delete: bool = False) -> None:
        """
        Checks that a prior call to `call_delete_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Expected message of the raised exception.
        :param assert_delete: Whether the `delete_one` method is expected to be called or not.
        """

        if not assert_delete:
            self.images_collection.find_one_and_delete.assert_not_called()
        else:
            self.images_collection.find_one_and_delete.assert_called_once_with(
                filter={"_id": ObjectId(self._delete_image_id)},
                projection={"object_key": True},
                session=self.mock_session,
            )

        assert str(self._delete_exception.value) == message


class TestDelete(DeleteDSL):
    """Tests for deleting an image."""

    def test_delete(self):
        """Test deleting an image."""
        image_id = str(ObjectId())

        self.mock_delete(image_id, IMAGE_IN_DATA_ALL_VALUES)
        self.call_delete(image_id)
        self.check_delete_success()

    def test_delete_non_existent_id(self):
        """Test deleting an image with a non-existent ID."""

        image_id = str(ObjectId())

        self.mock_delete(image_id, None)
        self.call_delete_expecting_error(image_id, MissingRecordError)
        self.check_delete_failed_with_exception(f"Requested Image was not found: {image_id}", assert_delete=True)

    def test_delete_invalid_id(self):
        """Test deleting an image with an invalid ID."""

        image_id = "invalid-id"

        self.call_delete_expecting_error(image_id, MissingRecordError)
        self.check_delete_failed_with_exception(f"Invalid image_id given: {image_id}")
