"""
Unit tests for the `ImageService` service.
"""

from test.mock_data import IMAGE_GET_DATA_ALL_VALUES, IMAGE_IN_DATA_ALL_VALUES, IMAGE_POST_METADATA_DATA_ALL_VALUES
from typing import List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from bson import ObjectId
from fastapi import UploadFile

from object_storage_api.core.exceptions import InvalidObjectIdError
from object_storage_api.models.image import ImageIn, ImageOut
from object_storage_api.schemas.image import ImagePostMetadataSchema, ImageSchema
from object_storage_api.services.image import ImageService


class ImageServiceDSL:
    """Base class for `ImageService` unit tests."""

    mock_image_repository: Mock
    mock_image_store: Mock
    image_service: ImageService

    mock_object_id: MagicMock
    mock_generate_thumbnail_base64_str: MagicMock

    @pytest.fixture(autouse=True)
    def setup(
        self,
        image_repository_mock,
        image_store_mock,
        image_service,
        # Ensures all created and modified times are mocked throughout
        # pylint: disable=unused-argument
        model_mixins_datetime_now_mock,
    ):
        """Setup fixtures"""

        self.mock_image_repository = image_repository_mock
        self.mock_image_store = image_store_mock
        self.image_service = image_service

        with patch("object_storage_api.services.image.ObjectId") as object_id_mock:
            self.mock_object_id = object_id_mock
            with patch(
                "object_storage_api.services.image.generate_thumbnail_base64_str"
            ) as generate_thumbnail_base64_str_mock:
                self.mock_generate_thumbnail_base64_str = generate_thumbnail_base64_str_mock
                yield


class CreateDSL(ImageServiceDSL):
    """Base class for `create` tests."""

    _image_post_metadata: ImagePostMetadataSchema
    _upload_file: UploadFile
    _expected_image_id: ObjectId
    _expected_image_in: ImageIn
    _expected_image: ImageSchema
    _created_image: ImageSchema
    _create_exception: pytest.ExceptionInfo

    def mock_create(self, image_post_metadata_data: dict) -> None:
        """
        Mocks repo & store methods appropriately to test the `create` service method.

        :param image_post_metadata_data: Dictionary containing the image metadata data as would be required for an
                                         `ImagePostMetadataSchema`.
        """

        self._image_post_metadata = ImagePostMetadataSchema(**image_post_metadata_data)
        self._upload_file = UploadFile(MagicMock(), size=100, filename="test.png", headers=MagicMock())

        self._expected_image_id = ObjectId()
        self.mock_object_id.return_value = self._expected_image_id

        # Thumbnail
        expected_thumbnail_base64 = "some_thumbnail"
        self.mock_generate_thumbnail_base64_str.return_value = expected_thumbnail_base64

        # Store
        expected_object_key = "some/object/key"
        self.mock_image_store.upload.return_value = expected_object_key

        # Expected model data with the object key defined (Ignore if invalid to avoid a premature error)
        if self._image_post_metadata.entity_id != "invalid-id":
            self._expected_image_in = ImageIn(
                **self._image_post_metadata.model_dump(),
                id=str(self._expected_image_id),
                object_key=expected_object_key,
                file_name=self._upload_file.filename,
                thumbnail_base64=expected_thumbnail_base64,
            )

            # Repo (The contents of the returned output model does not matter here as long as its valid)
            expected_image_out = ImageOut(**self._expected_image_in.model_dump(by_alias=True))
            self.mock_image_repository.create.return_value = expected_image_out

            self._expected_image = ImageSchema(**expected_image_out.model_dump())

    def call_create(self) -> None:
        """Calls the `ImageService` `create` method with the appropriate data from a prior call to
        `mock_create`."""

        self._created_image = self.image_service.create(self._image_post_metadata, self._upload_file)

    def call_create_expecting_error(self, error_type: type[BaseException]) -> None:
        """Calls the `ImageService` `create` method with the appropriate data from a prior call to
        `mock_create` while expecting an error to be raised..

        :param error_type: Expected exception to be raised.
        """

        with pytest.raises(error_type) as exc:
            self.image_service.create(self._image_post_metadata, self._upload_file)
        self._create_exception = exc

    def check_create_success(self) -> None:
        """Checks that a prior call to `call_create` worked as expected."""

        self.mock_generate_thumbnail_base64_str.assert_called_once_with(self._upload_file)
        self.mock_image_store.upload.assert_called_once_with(
            str(self._expected_image_id), self._image_post_metadata, self._upload_file
        )
        self.mock_image_repository.create.assert_called_once_with(self._expected_image_in)

        assert self._created_image == self._expected_image

    def check_create_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_create_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        """

        self.mock_generate_thumbnail_base64_str.assert_called_once_with(self._upload_file)
        self.mock_image_store.upload.assert_called_once_with(
            str(self._expected_image_id), self._image_post_metadata, self._upload_file
        )
        self.mock_image_repository.create.assert_not_called()

        assert str(self._create_exception.value) == message


class TestCreate(CreateDSL):
    """Tests for creating an image."""

    def test_create(self):
        """Test creating an image."""

        self.mock_create(IMAGE_POST_METADATA_DATA_ALL_VALUES)
        self.call_create()
        self.check_create_success()

    def test_create_with_invalid_entity_id(self):
        """Test creating an image with an invalid `entity_id`."""

        self.mock_create({**IMAGE_POST_METADATA_DATA_ALL_VALUES, "entity_id": "invalid-id"})
        self.call_create_expecting_error(InvalidObjectIdError)
        self.check_create_failed_with_exception("Invalid ObjectId value 'invalid-id'")


class ListDSL(ImageServiceDSL):
    """Base class for `list` tests."""

    _entity_id_filter: Optional[str]
    _primary_filter: Optional[str]
    _expected_images: List[ImageSchema]
    _obtained_images: List[ImageSchema]

    def mock_list(self, image_in_data: list[dict]) -> None:
        """Mocks repo methods appropriately to test the `list` service method."""

        self._expected_images = [
            ImageSchema(**ImageOut(**ImageIn(**image_in_data).model_dump()).model_dump())
            for image_in_data in image_in_data
        ]
        self.mock_image_repository.list.return_value = [
            ImageOut(**ImageIn(**image_in_data).model_dump()) for image_in_data in image_in_data
        ]

    def call_list(self, entity_id: Optional[str] = None, primary: Optional[bool] = None) -> None:
        """Calls the `ImageService` `list` method.

        :param entity_id: The ID of the entity to filter images by.
        :param primary: The primary value to filter images by.
        """
        self._entity_id_filter = entity_id
        self._primary_filter = primary
        self._obtained_images = self.image_service.list(entity_id=entity_id, primary=primary)

    def check_list_success(self) -> None:
        """Checks that a prior call to `call_list` worked as expected."""
        self.mock_image_repository.list.assert_called_once_with(self._entity_id_filter, self._primary_filter)
        assert self._obtained_images == self._expected_images


class TestList(ListDSL):
    """Tests for listing images."""

    def test_list(self):
        """Test listing images."""
        self.mock_list([IMAGE_IN_DATA_ALL_VALUES])
        self.call_list(entity_id=str(ObjectId()), primary=False)
        self.check_list_success()
