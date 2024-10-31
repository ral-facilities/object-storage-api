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
from bson import ObjectId
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

    def post_image(self, image_post_metadata_data: dict, file_name: str) -> Optional[str]:
        """
        Posts an image with the given metadata and a test image file and returns the id of the created image if
        successful.

        :param image_post_metadata_data: Dictionary containing the image metadata data as would be required for an
                                         `ImagePostMetadataSchema`.
        :param file_name: File name of the image to upload (relative to the 'test/files' directory).
        :return: ID of the created image (or `None` if not successful).
        """

        with open(f"test/files/{file_name}", mode="rb") as file:
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

        self.post_image(IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY, "image.jpg")
        self.check_post_image_success(IMAGE_GET_DATA_REQUIRED_VALUES_ONLY)

    def test_create_with_all_values_provided(self):
        """Test creating an image with all values provided."""

        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES, "image.jpg")
        self.check_post_image_success(IMAGE_GET_DATA_ALL_VALUES)

    def test_create_with_invalid_entity_id(self):
        """Test creating an image with an invalid `entity_id`."""

        self.post_image({**IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY, "entity_id": "invalid-id"}, "image.jpg")
        self.check_post_image_failed_with_detail(422, "Invalid `entity_id` given")

    def test_create_with_invalid_image_file(self):
        """Test creating an image with an invalid image file."""

        self.post_image(IMAGE_POST_METADATA_DATA_REQUIRED_VALUES_ONLY, "invalid_image.jpg")
        self.check_post_image_failed_with_detail(422, "File given is not a valid image")


class ListDSL(CreateDSL):
    """Base class for list tests."""

    _get_response_image: Response

    def get_images(self, filters: Optional[dict] = None) -> None:
        """Gets a list of images with the given filters.

        :param filters: Filters to use in the request."""
        self._get_response_image = self.test_client.get("/images", params=filters)

    def check_get_images_success(self, expected_images_get_data: list[dict]) -> None:
        """
        Checks that a prior call to `get_images` gave a successful response with the expected data returned.

        :param expected_images_get_data: List of dictionaries containing the expected image data as would
            be required for a `ImageSchema`.
        """
        assert self._get_response_image.status_code == 200
        assert self._get_response_image.json() == expected_images_get_data


class TestList(ListDSL):
    """Tests for getting a list of images."""

    def test_list_with_no_filters(self):
        """
        Test getting a list of all images with no filters provided.

        Posts an image and expects it to be returned.
        """

        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES, "image.jpg")
        expected_result = self._post_response_image.json()
        self.get_images()
        self.check_get_images_success([expected_result])

    def test_list_with_entity_id_filter(self):
        """
        Test getting a list of all images with an `entity_id` filter provided.

        Posts an image and then filter using the `entity_id`.
        """

        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES, "image.jpg")
        expected_result = self._post_response_image.json()
        entity_id = expected_result["entity_id"]
        self.get_images(filters={"entity_id": entity_id})
        self.check_get_images_success([expected_result])

    def test_list_with_entity_id_filter_with_no_matching_results(self):
        """Test getting a list of all images with an `entity_id` filter

        Posts nothing and expects no results."""
        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES, "image.jpg")
        self.get_images(filters={"entity_id": ObjectId()})
        self.check_get_images_success([])

    def test_list_with_primary_filter(self):
        """
        Test getting a list of all images with a `primary` filter provided.

        Posts an image and then filter using the `primary`.
        """

        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES, "image.jpg")
        expected_result = self._post_response_image.json()
        self.get_images(filters={"primary": False})
        self.check_get_images_success([expected_result])

    def test_list_with_primary_filter_with_no_matching_results(self):
        """Test getting a list of all images with a `primary` filter

        Posts nothing and expects no results."""
        self.post_image(IMAGE_POST_METADATA_DATA_ALL_VALUES, "image.jpg")
        self.get_images(filters={"primary": True})
        self.check_get_images_success([])
