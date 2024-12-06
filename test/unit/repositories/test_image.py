"""
Unit tests for the `ImageRepo` repository.
"""

from test.mock_data import IMAGE_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from typing import Optional
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId

from object_storage_api.core.exceptions import InvalidObjectIdError, MissingRecordError
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


class GetDSL(ImageRepoDSL):
    """Base class for `get` tests."""

    _obtained_image_id: str
    _expected_image_out: ImageOut
    _obtained_image_out: ImageOut
    _get_exception: pytest.ExceptionInfo

    def mock_get(self, image_id: str, image_in_data: dict) -> None:
        """
        Mocks database methods appropriately to test the `get` repo method.

        :param image_id: ID of the image to obtain.
        :param image_in_data: Dictionary containing the image data as would be required for an
            `ImageIn` database model (i.e. no created and modified times required).
        """
        if image_in_data:
            image_in_data["id"] = image_id
        self._expected_image_out = ImageOut(**ImageIn(**image_in_data).model_dump()) if image_in_data else None

        RepositoryTestHelpers.mock_find_one(
            self.images_collection, self._expected_image_out.model_dump() if self._expected_image_out else None
        )

    def call_get(self, image_id: str) -> None:
        """
        Calls the `ImageRepo` `get` method.

        :param image_id: The ID of the image to obtain.
        """
        self._obtained_image_id = image_id
        self._obtained_image_out = self.image_repository.get(image_id=image_id, session=self.mock_session)

    def call_get_expecting_error(self, image_id: str, error_type: type[BaseException]) -> None:
        """
        Calls the `ImageRepo` `get` method with the appropriate data from a prior call to `mock_get`
        while expecting an error to be raised.

        :param image_id: ID of the image to be obtained.
        :param error_type: Expected exception to be raised.
        """
        self._obtained_image_id = image_id
        with pytest.raises(error_type) as exc:
            self.image_repository.get(image_id, session=self.mock_session)
        self._get_exception = exc

    def check_get_success(self) -> None:
        """Checks that a prior call to `call_get` worked as expected."""

        self.images_collection.find_one.assert_called_once_with(
            {"_id": ObjectId(self._obtained_image_id)}, session=self.mock_session
        )
        assert self._obtained_image_out == self._expected_image_out

    def check_get_failed_with_exception(self, message: str, assert_find: bool = False) -> None:
        """
        Checks that a prior call to `call_get_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param image_id: ID of the expected image to appear in the exception detail.
        :param assert_find: If `True` it asserts whether a `find_one` call was made,
            else it asserts that no call was made.
        """
        if assert_find:
            self.images_collection.find_one.assert_called_once_with(
                {"_id": ObjectId(self._obtained_image_id)}, session=self.mock_session
            )
        else:
            self.images_collection.find_one.assert_not_called()

        assert str(self._get_exception.value) == message


class TestGet(GetDSL):
    """Tests for getting images."""

    def test_get(self):
        """Test getting an image."""

        image_id = str(ObjectId())

        self.mock_get(image_id, IMAGE_IN_DATA_ALL_VALUES)
        self.call_get(image_id)
        self.check_get_success()

    def test_get_with_non_existent_id(self):
        """Test getting an image with a non-existent image ID."""

        image_id = str(ObjectId())

        self.mock_get(image_id, None)
        self.call_get_expecting_error(image_id, MissingRecordError)
        self.check_get_failed_with_exception(f"No image found with ID: {image_id}", True)

    def test_get_with_invalid_id(self):
        """Test getting an image with an invalid image ID."""
        image_id = "invalid-id"

        self.mock_get(image_id, None)
        self.call_get_expecting_error(image_id, InvalidObjectIdError)
        self.check_get_failed_with_exception(f"Invalid ObjectId value '{image_id}'")


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


class UpdateDSL(ImageRepoDSL):
    """Base class for `update` tests."""

    _image_in: ImageIn
    _expected_image_out: ImageOut
    _updated_image_id: str
    _updated_image: ImageOut
    _update_exception: pytest.ExceptionInfo

    def set_update_data(self, new_image_in_data: dict):
        """
        Assigns the update data to use during a call to `call_update`.

        :param new_image_in_data: New image data as would be required for an `ImageIn` database model to supply to the
                                 `ImageRepo` `update` method.
        """
        self._image_in = ImageIn(**new_image_in_data)

    def mock_update(
        self,
        image_id: str,
        new_image_in_data: dict,
    ) -> None:
        """
        Mocks database methods appropriately to test the `update` repo method.

        :param image_id: ID of the image that will be updated.
        :param new_image_in_data: Dictionary containing the new image data as would be required for an `ImageIn` database
                                 model (i.e. no created and modified times required).
        """
        self.set_update_data(new_image_in_data)

        self._expected_image_out = ImageOut(**self._image_in.model_dump())
        RepositoryTestHelpers.mock_find_one(self.images_collection, self._expected_image_out.model_dump(by_alias=True))

    def call_update(self, image_id: str) -> None:
        """
        Calls the `ImageRepo` `update` method with the appropriate data from a prior call to `mock_update`
        (or `set_update_data`).

        :param image_id: ID of the image to be updated.
        """

        self._updated_image_id = image_id
        self._updated_image = self.image_repository.update(image_id, self._image_in, session=self.mock_session)

    def call_update_expecting_error(self, image_id: str, error_type: type[BaseException]) -> None:
        """
        Calls the `ImageRepo` `update` method with the appropriate data from a prior call to `mock_update`
        (or `set_update_data`) while expecting an error to be raised.

        :param image_id: ID of the image to be updated.
        :param error_type: Expected exception to be raised.
        """

        with pytest.raises(error_type) as exc:
            self.image_repository.update(image_id, self._image_in)
        self._update_exception = exc

    def check_update_success(self) -> None:
        """Checks that a prior call to `call_update` worked as expected."""

        self.images_collection.update_one.assert_called_once_with(
            {
                "_id": ObjectId(self._updated_image_id),
            },
            {
                "$set": self._image_in.model_dump(by_alias=True),
            },
            session=self.mock_session,
        )

        assert self._updated_image == self._expected_image_out

    def check_update_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_update_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Expected message of the raised exception.
        """

        self.images_collection.update_one.assert_not_called()

        assert str(self._update_exception.value) == message


class TestUpdate(UpdateDSL):
    """Tests for updating an image."""

    def test_update(self):
        """Test updating an image."""

        image_id = str(ObjectId())

        self.mock_update(image_id, IMAGE_IN_DATA_ALL_VALUES)
        self.call_update(image_id)
        self.check_update_success()

    def test_update_with_invalid_id(self):
        """Test updating an image with an invalid ID."""

        image_id = "invalid-id"

        self.set_update_data(IMAGE_IN_DATA_ALL_VALUES)
        self.call_update_expecting_error(image_id, InvalidObjectIdError)
        self.check_update_failed_with_exception("Invalid ObjectId value 'invalid-id'")
