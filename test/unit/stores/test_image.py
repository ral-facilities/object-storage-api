"""
Unit tests for the `ImageStore` store.
"""

from test.mock_data import IMAGE_POST_METADATA_DATA_ALL_VALUES
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import UploadFile

from object_storage_api.core.object_store import object_storage_config
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

        :param image_post_metadata_data: Dictionary containing the attachment data as would be required for an
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
