"""
Unit tests for the `ImageStore` store.
"""

from test.mock_data import IMAGE_IN_DATA_ALL_VALUES, IMAGE_POST_METADATA_DATA_ALL_VALUES
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import UploadFile
from pydantic import HttpUrl

from object_storage_api.core.object_store import object_storage_config
from object_storage_api.models.image import ImageIn, ImageOut
from object_storage_api.schemas.image import ImagePostMetadataSchema
from object_storage_api.stores.image import ImageStore


class ImageStoreDSL:
    """Base class for `ImageStore` unit tests."""

    mock_s3_client: MagicMock
    image_store: ImageStore

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup fixtures"""

        with patch("object_storage_api.stores.image.s3_client") as s3_client_mock:
            self.mock_s3_client = s3_client_mock
            self.image_store = ImageStore()
            yield


class UploadDSL(ImageStoreDSL):
    """Base class for `upload` tests."""

    _image_post_metadata: ImagePostMetadataSchema
    _upload_file: UploadFile
    _image_id: str
    _expected_object_key: str
    _obtained_object_key: str

    def mock_upload(self, image_post_metadata_data: dict) -> None:
        """
        Mocks object store methods appropriately to test the `upload` store method.

        :param image_post_metadata_data: Dictionary containing the image metadata data as would be required for an
                                         `ImagePostMetadataSchema`.
        """

        self._image_post_metadata = ImagePostMetadataSchema(**image_post_metadata_data)
        self._upload_file = UploadFile(MagicMock(), size=100, filename="test.png", headers=MagicMock())
        self._image_id = str(ObjectId())

        self._expected_object_key = f"images/{self._image_post_metadata.entity_id}/{self._image_id}"

    def call_upload(self) -> None:
        """Calls the `ImageStore` `upload` method with the appropriate data from a prior call to `mock_upload`."""

        self._obtained_object_key = self.image_store.upload(
            self._image_id, self._image_post_metadata, self._upload_file
        )

    def check_upload_success(self) -> None:
        """Checks that a prior call to `call_upload` worked as expected."""

        self.mock_s3_client.upload_fileobj.assert_called_once_with(
            self._upload_file.file,
            Bucket=object_storage_config.bucket_name.get_secret_value(),
            Key=self._expected_object_key,
            ExtraArgs={"ContentType": self._upload_file.content_type},
        )

        assert self._obtained_object_key == self._expected_object_key


class TestUpload(UploadDSL):
    """Tests for uploading an image."""

    def test_upload(self):
        """Test uploading an image."""

        self.mock_upload(IMAGE_POST_METADATA_DATA_ALL_VALUES)
        self.call_upload()
        self.check_upload_success()


class CreatePresignedURLDSL(ImageStoreDSL):
    """Base class for `create` tests."""

    _image_out: ImageOut
    _expected_presigned_url: HttpUrl
    _obtained_presigned_url: HttpUrl

    def mock_create_presigned_get(self, image_in_data: dict) -> None:
        """
        Mocks object store methods appropriately to test the `create_presigned_get` store method.

        :param image_in_data: Dictionary containing the image  data as would be required for an
        `ImageIn`.
        """
        self._image_out = ImageOut(**ImageIn(**image_in_data).model_dump())

        # Mock presigned url generation
        self._expected_presigned_url = "example_presigned_url"
        self.mock_s3_client.generate_presigned_url.return_value = self._expected_presigned_url

    def call_create_presigned_get(self) -> None:
        """Calls the `ImageStore` `create_presigned_get` method with the appropriate data from a prior call to
        `mock_create_presigned_get`."""

        self._obtained_presigned_url = self.image_store.create_presigned_get(self._image_out)

    def check_create_presigned_get_success(self) -> None:
        """Checks that a prior call to `call_create_presigned_get` worked as expected."""

        self.mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": object_storage_config.bucket_name.get_secret_value(),
                "Key": self._image_out.object_key,
                "ResponseContentDisposition": f'inline; filename="{self._image_out.file_name}"',
            },
            ExpiresIn=object_storage_config.presigned_url_expiry_seconds,
        )

        assert self._obtained_presigned_url == self._expected_presigned_url


class TestCreatePresignedURL(CreatePresignedURLDSL):
    """Tests for creating a presigned url for an image."""

    def test_create_presigned_get(self):
        """Test creating a presigned url for an image."""

        self.mock_create_presigned_get(IMAGE_IN_DATA_ALL_VALUES)
        self.call_create_presigned_get()
        self.check_create_presigned_get_success()
