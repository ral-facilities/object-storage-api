"""
Unit tests for the `ImageService` service.
"""

from test.mock_data import (
    IMAGE_IN_DATA_ALL_VALUES,
    IMAGE_PATCH_METADATA_DATA_ALL_VALUES,
    IMAGE_POST_METADATA_DATA_ALL_VALUES,
)
from typing import List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from bson import ObjectId
from fastapi import UploadFile

from object_storage_api.core.exceptions import (
    FileTypeMismatchException,
    InvalidObjectIdError,
    UnsupportedFileExtensionException,
)
from object_storage_api.models.image import ImageIn, ImageOut
from object_storage_api.schemas.image import (
    ImageMetadataSchema,
    ImagePatchMetadataSchema,
    ImagePostMetadataSchema,
    ImageSchema,
)
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
    _expected_image: ImageMetadataSchema
    _created_image: ImageMetadataSchema
    _create_exception: pytest.ExceptionInfo

    def mock_create(self, image_post_metadata_data: dict, filename: str) -> None:
        """
        Mocks repo & store methods appropriately to test the `create` service method.

        :param image_post_metadata_data: Dictionary containing the image metadata data as would be required for an
                                         `ImagePostMetadataSchema`.
        :param filename: Filename of the image.
        """

        self._image_post_metadata = ImagePostMetadataSchema(**image_post_metadata_data)
        header = {"content-type": "image/png"}
        self._upload_file = UploadFile(MagicMock(), size=100, filename=filename, headers=header)

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

            self._expected_image = ImageMetadataSchema(**expected_image_out.model_dump())

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

    def check_create_failed_with_exception(self, message: str, assert_checks: bool = True) -> None:
        """
        Checks that a prior call to `call_create_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        :param assert_checks: Whether the `generate_thumbnail_base64_str` and `upload` method are expected to be called.
        """
        if assert_checks:
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

        self.mock_create(IMAGE_POST_METADATA_DATA_ALL_VALUES, "test.png")
        self.call_create()
        self.check_create_success()

    def test_create_with_file_extension_content_type_mismatch(self):
        """Test creating an image with an inconsistent file extension and content type."""

        self.mock_create(IMAGE_POST_METADATA_DATA_ALL_VALUES, "test.jpeg")
        self.call_create_expecting_error(FileTypeMismatchException)
        self.check_create_failed_with_exception(
            f"File extension of '{self._upload_file.filename}' does not match "
            f"content type '{self._upload_file.content_type}'",
            assert_checks=False,
        )

    def test_create_with_file_extension_not_supported(self):
        """Test creating an image with a file extension that is not supported."""
        self.mock_create(IMAGE_POST_METADATA_DATA_ALL_VALUES, "test.gif")
        self.call_create_expecting_error(UnsupportedFileExtensionException)
        self.check_create_failed_with_exception(
            f"File extension of '{self._upload_file.filename}' is not supported", assert_checks=False
        )

    def test_create_with_invalid_entity_id(self):
        """Test creating an image with an invalid `entity_id`."""

        self.mock_create({**IMAGE_POST_METADATA_DATA_ALL_VALUES, "entity_id": "invalid-id"}, "test.png")
        self.call_create_expecting_error(InvalidObjectIdError)
        self.check_create_failed_with_exception("Invalid ObjectId value 'invalid-id'")


class GetDSL(ImageServiceDSL):
    """Base class for `get` tests."""

    _obtained_image_id: str
    _expected_image_out: ImageOut
    _expected_image: ImageSchema
    _obtained_image: ImageSchema

    def mock_get(self) -> None:
        """Mocks repo methods appropriately to test the `get` service method."""

        self._expected_image_out = ImageOut(**ImageIn(**IMAGE_IN_DATA_ALL_VALUES).model_dump())
        self.mock_image_repository.get.return_value = self._expected_image_out
        self.mock_image_store.create_presigned_get.return_value = (
            "https://fakepresignedurl.co.uk/inline",
            "https://fakepresignedurl.co.uk/attachment",
        )
        self._expected_image = ImageSchema(
            **self._expected_image_out.model_dump(),
            view_url="https://fakepresignedurl.co.uk/inline",
            download_url="https://fakepresignedurl.co.uk/attachment",
        )

    def call_get(self, image_id: str) -> None:
        """
        Calls the `ImageService` `get` method.

        :param image_id: The ID of the image to obtain.
        """
        self._obtained_image_id = image_id
        self._obtained_image = self.image_service.get(image_id=image_id)

    def check_get_success(self) -> None:
        """Checks that a prior call to `call_get` worked as expected."""
        self.mock_image_repository.get.assert_called_once_with(image_id=self._obtained_image_id)
        self.mock_image_store.create_presigned_get.assert_called_once_with(self._expected_image_out)
        assert self._obtained_image == self._expected_image


class TestGet(GetDSL):
    """Tests for getting images."""

    def test_get(self):
        """Test getting images."""
        self.mock_get()
        self.call_get(str(ObjectId()))
        self.check_get_success()


class ListDSL(ImageServiceDSL):
    """Base class for `list` tests."""

    _entity_id_filter: Optional[str]
    _primary_filter: Optional[str]
    _expected_images: List[ImageMetadataSchema]
    _obtained_images: List[ImageMetadataSchema]

    def mock_list(self) -> None:
        """Mocks repo methods appropriately to test the `list` service method."""

        # Just returns the result after converting it to the schemas currently, so actual value doesn't matter here
        images_out = [ImageOut(**ImageIn(**IMAGE_IN_DATA_ALL_VALUES).model_dump())]
        self.mock_image_repository.list.return_value = images_out
        self._expected_images = [ImageMetadataSchema(**image_out.model_dump()) for image_out in images_out]

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
        self.mock_list()
        self.call_list(entity_id=str(ObjectId()), primary=False)
        self.check_list_success()


class UpdateDSL(ImageServiceDSL):
    """Base class for `update` tests."""

    _stored_image: Optional[ImageOut]
    _image_patch: ImagePatchMetadataSchema
    _expected_image_in: ImageIn
    _expected_image_out: ImageOut
    _updated_image_id: str
    _updated_image: MagicMock
    _update_exception: pytest.ExceptionInfo

    def mock_update(self, image_patch_data: dict, stored_image_post_data: Optional[dict]) -> None:
        """
        Mocks the repository methods appropriately to test the `update` service method.

        :param image_patch_data: Dictionary containing the patch data as would be required for an
            `ImagePatchMetadataSchema` (i.e. no created and modified times required).
        :param stored_image_post_data: Dictionary containing the image data for the existing stored
            image as would be required for an `ImagePostMetadataSchema` (i.e. no created and modified
            times required).
        """
        # Stored image
        self._stored_image = (
            ImageOut(
                **ImageIn(
                    **stored_image_post_data,
                ).model_dump(),
            )
            if stored_image_post_data
            else None
        )
        self.mock_image_repository.get.return_value = self._stored_image

        # Patch schema
        self._image_patch = ImagePatchMetadataSchema(**image_patch_data)

        # Construct the expected input for the repository
        merged_image_data = {**(stored_image_post_data or {}), **image_patch_data}
        self._expected_image_in = ImageIn(**merged_image_data)

        # Updated image
        image_out = ImageOut(
            **self._expected_image_in.model_dump(),
        )

        self.mock_image_repository.update.return_value = image_out

        self._expected_image_out = ImageMetadataSchema(**image_out.model_dump())

    def call_update(self, image_id: str) -> None:
        """
        Class the `ImageService` `update` method with the appropriate data from a prior call to `mock_update`.

        :param image_id: ID of the image to be updated.
        """
        self._updated_image_id = image_id
        self._updated_image = self.image_service.update(image_id, self._image_patch)

    def call_update_expecting_error(self, image_id: str, error_type: type[BaseException]) -> None:
        """
        Class the `ImageService` `update` method with the appropriate data from a prior call to `mock_update`,
        while expecting an error to be raised.

        :param image_id: ID of the image to be updated.
        :param error_type: Expected exception to be raised.
        """

        self._updated_image_id = image_id
        with pytest.raises(error_type) as exc:
            self.image_service.update(image_id, self._image_patch)
        self._update_exception = exc

    def check_update_success(self) -> None:
        """Checks that a prior call to `call_update` worked as expected."""
        # Ensure obtained old image
        self.mock_image_repository.get.assert_called_once_with(image_id=self._updated_image_id)

        # Ensure updated with expected data
        self.mock_image_repository.update.assert_called_once_with(
            image_id=self._updated_image_id,
            image=self._expected_image_in,
            update_primary=self._expected_image_out.primary,
        )

        assert self._updated_image == self._expected_image_out

    def check_update_failed_with_exception(self, message: str) -> None:
        """
        Checks that a prior call to `call_update_expecting_error` worked as expected, raising an exception
        with the correct message.

        :param message: Message of the raised exception.
        """

        self.mock_image_repository.get.assert_called_once_with(image_id=self._updated_image_id)
        self.mock_image_repository.update.assert_not_called()

        assert str(self._update_exception.value) == message


class TestUpdate(UpdateDSL):
    """Tests for updating an image."""

    def test_update(self):
        """Test updating all fields of an image."""
        image_id = str(ObjectId())

        self.mock_update(
            image_patch_data=IMAGE_PATCH_METADATA_DATA_ALL_VALUES,
            stored_image_post_data=IMAGE_IN_DATA_ALL_VALUES,
        )
        self.call_update(image_id)
        self.check_update_success()

    def test_update_primary(self):
        """Test updating primary from false to true for an image."""
        image_id = str(ObjectId())

        self.mock_update(
            image_patch_data={**IMAGE_PATCH_METADATA_DATA_ALL_VALUES, "primary": True},
            stored_image_post_data=IMAGE_IN_DATA_ALL_VALUES,
        )
        self.call_update(image_id)
        self.check_update_success()

    def test_update_with_file_extension_content_type_mismatch(self):
        """Test updating filename to one with a mismatched file extension."""
        image_id = str(ObjectId())

        self.mock_update(
            image_patch_data={**IMAGE_PATCH_METADATA_DATA_ALL_VALUES, "file_name": "picture.png"},
            stored_image_post_data=IMAGE_IN_DATA_ALL_VALUES,
        )
        self.call_update_expecting_error(image_id, FileTypeMismatchException)
        self.check_update_failed_with_exception(
            f"Patch filename extension of '{self._image_patch.file_name}' does not match "
            f"that of the stored image '{self._stored_image.file_name}'"
        )


class DeleteDSL(ImageServiceDSL):
    """Base class for `delete` tests."""

    _delete_image_id: str
    _expected_image_out: ImageOut
    _delete_image_id: str
    _delete_image_object_key: str

    def mock_delete(self, image_in_data: dict) -> None:
        """
        Mocks repo methods appropriately to test the `delete` service method.

        :param image_in_data: Dictionary containing the image data as would be required for an `ImageIn`
                                   database model (i.e. no created and modified times required).
        """
        self._expected_image_out = ImageOut(**ImageIn(**image_in_data).model_dump())
        self.mock_image_repository.get.return_value = self._expected_image_out
        self._delete_image_id = self._expected_image_out.id
        self._delete_image_object_key = self._expected_image_out.object_key

    def call_delete(self) -> None:
        """Calls the `ImageService` `delete` method."""

        self.image_service.delete(self._delete_image_id)

    def check_delete_success(self) -> None:
        """Checks that a prior call to `call_delete` worked as expected."""

        self.mock_image_store.delete.assert_called_once_with(self._delete_image_object_key)
        self.mock_image_repository.delete.assert_called_once_with(self._delete_image_id)


class TestDelete(DeleteDSL):
    """Tests for deleting an image."""

    def test_delete(self):
        """Test for deleting an image."""
        self.mock_delete(IMAGE_IN_DATA_ALL_VALUES)
        self.call_delete()
        self.check_delete_success()


class DeleteByEntityIdDSL(ImageServiceDSL):
    """Base class for `delete_by_entity_id` tests."""

    _expected_images_out: list[ImageOut]
    _delete_entity_id: str
    _delete_image_object_keys: list[str]

    def mock_delete_by_entity_id(self, images_in_data: list[dict]) -> None:
        """
        Mocks repo methods appropriately to test the `delete_by_entity_id` service method.

        :param images_in_data: List of dictionaries containing the image data as would be required for an `ImageIn`
            database model (i.e. no created and modified times required).
        """
        self._expected_images_out = [
            ImageOut(**ImageIn(**image_in_data).model_dump()) for image_in_data in images_in_data
        ]
        self.mock_image_repository.list.return_value = self._expected_images_out
        self._delete_entity_id = self._expected_images_out[0].id if self._expected_images_out else str(ObjectId())
        self._delete_image_object_keys = [
            expected_image_out.object_key for expected_image_out in self._expected_images_out
        ]

    def call_delete_by_entity_id(self) -> None:
        """Calls the `ImageService` `delete_by_entity_id` method."""
        self.image_service.delete_by_entity_id(self._delete_entity_id)

    def check_delete_by_entity_id_success(self, assert_delete: bool = True) -> None:
        """
        Checks that a prior call to `call_delete_by_entity_id` worked as expected.

        :param assert_delete: Whether the `delete_many` store method and `delete_by_entity_id` repo method are expected
            to be called or not.
        """
        if assert_delete:
            self.mock_image_store.delete_many.assert_called_once_with(self._delete_image_object_keys)
            self.mock_image_repository.delete_by_entity_id.assert_called_once_with(self._delete_entity_id)
        else:
            self.mock_image_store.delete_many.assert_not_called()
            self.mock_image_repository.delete_by_entity_id.assert_not_called()


# Expect some duplicate code inside tests as the tests for the different entities can be very similar
# pylint: disable=duplicate-code


class TestDeleteByEntityId(DeleteByEntityIdDSL):
    """Tests for deleting images by `entity_id`."""

    def test_delete_by_entity_id(self):
        """Test deleting images."""
        self.mock_delete_by_entity_id([IMAGE_IN_DATA_ALL_VALUES])
        self.call_delete_by_entity_id()
        self.check_delete_by_entity_id_success()

    def test_delete_by_entity_id_non_existent_id(self):
        """Test deleting images with a non-existent `entity_id`."""
        self.mock_delete_by_entity_id([])
        self.call_delete_by_entity_id()
        self.check_delete_by_entity_id_success(False)


# pylint: enable=duplicate-code
