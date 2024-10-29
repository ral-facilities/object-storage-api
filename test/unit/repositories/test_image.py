"""
Unit tests for the `ImageRepo` repository.
"""

from test.mock_data import IMAGE_IN_DATA_ALL_VALUES
from test.unit.repositories.conftest import RepositoryTestHelpers
from typing import Optional
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId

from object_storage_api.core.custom_object_id import CustomObjectId
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
    _obtained_image_out: list[ImageOut]

    def mock_list(self, image_in_data: list[dict], query: dict = None) -> None:
        """
        Mocks database methods appropriately to test the `list` repo method.

        :param image_in_data: List of dictionaries containing the image data as would be required for an
            `ImageIn` database model (i.e. no ID or created and modified times required).
        """
        self._expected_image_out = [
            ImageOut(**ImageIn(**image_in_data).model_dump()) for image_in_data in image_in_data
        ]

        RepositoryTestHelpers.mock_find(
            self.images_collection, [image_out.model_dump() for image_out in self._expected_image_out], query=query
        )

    def call_list(self, entity_id: Optional[str], primary: Optional[bool]) -> None:
        """Calls the `ImageRepo` `list method` method."""
        self._obtained_image_out = self.image_repository.list(
            session=self.mock_session, entity_id=entity_id, primary=primary
        )

    def check_list_success(self, query: Optional[dict] = None) -> None:
        """Checks that a prior call to `call_list` worked as expected."""
        self.images_collection.find.assert_called_once_with(session=self.mock_session, query=query)
        assert self._obtained_image_out == self._expected_image_out


class TestList(ListDSL):
    """Tests for listing images"""

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

    def test_list(self):
        """Test listing all images with an entity_id argument."""
        query = {"entity_id": IMAGE_IN_DATA_ALL_VALUES["entity_id"]}
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES], query=query)
        self.call_list(entity_id=query["entity_id"])
        self.check_list_success(query)

    def test_list(self):
        """Test listing all images with a primary argument."""
        query = {"primary": False}
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES], query=query)
        self.call_list(primary=query["primary"])
        self.check_list_success(query)

    def test_list(self):
        """Test listing all images with an entity_id and primary argument."""
        query = {"entity_id": IMAGE_IN_DATA_ALL_VALUES["entity_id"], "primary": False}
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES], query=query)
        self.call_list(primary=query["primary"], entity_id=query["entity_id"])
        self.check_list_success(query)
