"""
End-to-End tests for the attachment router.
"""

from test.mock_data import (
    ATTACHMENT_POST_DATA_ALL_VALUES,
    ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY,
    ATTACHMENT_POST_RESPONSE_DATA_ALL_VALUES,
    ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY,
)
from typing import Optional

import pytest
import requests
from fastapi.testclient import TestClient
from httpx import Response


class CreateDSL:
    """Base class for create tests."""

    test_client: TestClient

    _post_response_attachment: Response
    _upload_response_attachment: Response

    @pytest.fixture(autouse=True)
    def setup(self, test_client):
        """Setup fixtures"""

        self.test_client = test_client

    def post_attachment(self, attachment_post_data: dict) -> Optional[str]:
        """
        Posts an attachment with the given data and returns the id of the created attachment if successful.

        :param attachment_post_data: Dictionary containing the attachment data as would be required for an
                                     `AttachmentPostSchema`.
        :return: ID of the created attachment (or `None` if not successful).
        """

        self._post_response_attachment = self.test_client.post("/attachments", json=attachment_post_data)
        return (
            self._post_response_attachment.json()["id"] if self._post_response_attachment.status_code == 201 else None
        )

    def upload_attachment(self) -> None:
        """
        Uploads an attachment to the last posted attachment's `upload_url`.
        """

        self._upload_response_attachment = requests.put(
            self._post_response_attachment.json()["upload_url"],
            data="Some test data\nnew line",
            headers={"Content-Type": "multipart/form-data"},
            timeout=5,
        )

    def check_post_attachment_success(self, expected_post_response_data: dict) -> None:
        """
        Checks that a prior call to `post_attachment` gave a successful response with the expected data returned.

        :param expected_post_response_data: Dictionary containing the expected attachment data returned as would be
                                             required for a `AttachmentPostResponseSchema`.
        """

        assert self._post_response_attachment.status_code == 201
        assert self._post_response_attachment.json() == expected_post_response_data

    def check_post_attachment_failed_with_detail(self, status_code: int, detail: str) -> None:
        """
        Checks that a prior call to `post_attachment` gave a failed response with the expected code and error message.

        :param status_code: Expected status code of the response.
        :param detail: Expected detail given in the response.
        """

        assert self._post_response_attachment.status_code == status_code
        assert self._post_response_attachment.json()["detail"] == detail

    def check_upload_attachment_success(self) -> None:
        """
        Checks that a prior call to `upload_attachment` gave a successful response with response returned.
        """

        assert self._upload_response_attachment.status_code == 200


class TestCreate(CreateDSL):
    """Tests for creating an attachment."""

    def test_create_with_only_required_values_provided(self):
        """Test creating an attachment with only required values provided."""

        self.post_attachment(ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY)
        self.check_post_attachment_success(ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY)
        self.upload_attachment()
        self.check_upload_attachment_success()

    def test_create_with_all_values_provided(self):
        """Test creating an attachment with all values provided."""

        self.post_attachment(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.check_post_attachment_success(ATTACHMENT_POST_RESPONSE_DATA_ALL_VALUES)
        self.upload_attachment()
        self.check_upload_attachment_success()

    def test_create_with_invalid_entity_id(self):
        """Test creating an attachment with an invalid `entity_id`."""

        self.post_attachment({**ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY, "entity_id": "invalid-id"})
        self.check_post_attachment_failed_with_detail(422, "Invalid `entity_id` given")
