"""
End-to-End tests for the image router.
"""

from test.mock_data import (
    IMAGE_GET_DATA_ALL_VALUES,
    IMAGE_GET_DATA_REQUIRED_VALUES_ONLY,
    IMAGE_POST_METADATA_DATA_ALL_VALUES,
    IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY,
)
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from httpx import Response


class CreateDSL:
    """Base class for create tests."""

    test_client: TestClient

    _post_response_image: Response
    _upload_response_image: Response

    @pytest.fixture(autouse=True)
    def setup(self, test_client):
        """Setup fixtures"""

        self.test_client = test_client

    def post_image(self, image_post_metadata_data: dict) -> Optional[str]:
        """
        Posts an image with the given metadata and a test image file and returns the id of the created image if
        successful.

        :param image_post_metadata_data: Dictionary containing the image metadata data as would be required for an
                                         `ImagePostMetadataSchema`.
        :return: ID of the created image (or `None` if not successful).
        """

        with open("test/e2e/files/image.jpg", mode="rb") as file:
            self._post_response_image = self.test_client.post(
                "/images", data={**image_post_metadata_data}, files={"upload_file": file}
            )
        return self._post_response_image.json()["id"] if self._post_response_image.status_code == 201 else None

    def check_post_image_success(self, expected_image_get_data: dict) -> None:
        """
        Checks that a prior call to `post_image` gave a successful response with the expected data returned.

        :param expected_image_get_data: Dictionary containing the expected image data returned as would be
                                        required for an `ImageSchema`.
        """

        assert self._post_response_image.status_code == 201
        assert self._post_response_image.json() == {**expected_image_get_data, "file_name": "image.jpg"}

    def check_post_image_failed_with_detail(self, status_code: int, detail: str) -> None:
        """
        Checks that a prior call to `post_image` gave a failed response with the expected code and error message.

        :param status_code: Expected status code of the response.
        :param detail: Expected detail given in the response.
        """

        assert self._post_response_image.status_code == status_code
        assert self._post_response_image.json()["detail"] == detail


class TestCreate(CreateDSL):
    """Tests for creating an image."""

    def test_create_with_only_required_values_provided(self):
        """Test creating an image with only required values provided."""

        self.post_image(IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY)
        self.check_post_image_success(IMAGE_GET_DATA_REQUIRED_VALUES_ONLY)

    def test_create_with_all_values_provided(self):
        """Test creating an image with all values provided."""

        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES)
        self.check_post_image_success(IMAGE_GET_DATA_ALL_VALUES)

    def test_create_with_invalid_entity_id(self):
        """Test creating an image with an invalid `entity_id`."""

        self.post_image({**IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY, "entity_id": "invalid-id"})
        self.check_post_image_failed_with_detail(422, "Invalid `entity_id` given")
