"""
Unit tests for the `ImageRepo` repository.
"""

from test.mock_data import IMAGE_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from unittest.mock import MagicMock, Mock

import pytest

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
