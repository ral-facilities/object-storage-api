"""
End-to-End tests for the attachment router.
"""

from test.mock_data import (
    ATTACHMENT_GET_DATA_ALL_VALUES,
    ATTACHMENT_GET_METADATA_DATA_ALL_VALUES_AFTER_PATCH,
    ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES,
    ATTACHMENT_POST_DATA_ALL_VALUES,
    ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY,
    ATTACHMENT_POST_RESPONSE_DATA_ALL_VALUES,
    ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY,
)
from typing import Optional

import pytest
from bson import ObjectId
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

    def upload_attachment(self, file_data: str = "Some test data\nnew line") -> None:
        """
        Uploads an attachment to the last posted attachment's `upload_url`.

        :param file_data: File data to upload.
        """

        upload_info = self._post_response_attachment.json()["upload_info"]
        self._upload_response_attachment = requests.post(
            upload_info["url"],
            files={"file": file_data},
            data=upload_info["fields"],
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

        assert self._upload_response_attachment.status_code == 204

    def check_upload_attachment_failed_with_contents(self, status_code: int, expected_contents: str) -> None:
        """
        Checks that a prior call to `upload_attachment` gave a failed response with expected code and contents.

        :param status_code: Expected status code of the response.
        :param expected_contents: Expected contents expected to be found within the content of the failed request.
        """

        assert self._upload_response_attachment.status_code == status_code
        assert expected_contents in self._upload_response_attachment.content.decode()


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

    def test_create_with_file_too_large(self):
        """Test creating an attachment with file that is too large."""

        self.post_attachment(ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY)
        self.check_post_attachment_success(ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY)
        self.upload_attachment(file_data="Some test data\n" * 10)
        self.check_upload_attachment_failed_with_contents(400, "EntityTooLarge")

    def test_create_with_invalid_entity_id(self):
        """Test creating an attachment with an invalid `entity_id`."""

        self.post_attachment({**ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY, "entity_id": "invalid-id"})
        self.check_post_attachment_failed_with_detail(422, "Invalid `entity_id` given")


class ListDSL(CreateDSL):
    """Base class for list tests."""

    _get_response_attachment: Response

    def get_attachments(self, filters: Optional[dict] = None) -> None:
        """
        Gets a list of attachments with the given filters.

        :param filters: Filters to use in the request.
        """
        self._get_response_attachment = self.test_client.get("/attachments", params=filters)

    def post_test_attachments(self) -> list[dict]:
        """
        Posts three attachments. The first two attachments have the same entity ID, the last attachment has a different
        one.

        :return: List of dictionaries containing the expected item data returned from a get endpoint in
                 the form of an `AttachmentMetadataSchema`.
        """
        entity_id_a, entity_id_b = (str(ObjectId()) for _ in range(2))

        # First item
        attachment_a_id = self.post_attachment(
            {
                **ATTACHMENT_POST_DATA_ALL_VALUES,
                "entity_id": entity_id_a,
            },
        )

        # Second item
        attachment_b_id = self.post_attachment(
            {
                **ATTACHMENT_POST_DATA_ALL_VALUES,
                "entity_id": entity_id_a,
            },
        )

        # Third item
        attachment_c_id = self.post_attachment(
            {
                **ATTACHMENT_POST_DATA_ALL_VALUES,
                "entity_id": entity_id_b,
            },
        )

        return [
            {**ATTACHMENT_GET_DATA_ALL_VALUES, "entity_id": entity_id_a, "id": attachment_a_id},
            {**ATTACHMENT_GET_DATA_ALL_VALUES, "entity_id": entity_id_a, "id": attachment_b_id},
            {**ATTACHMENT_GET_DATA_ALL_VALUES, "entity_id": entity_id_b, "id": attachment_c_id},
        ]

    def check_get_attachments_success(self, expected_attachments_get_data: list[dict]) -> None:
        """
        Checks that a prior call to `get_attachments` gave a successful response with the expected data returned.

        :param expected_attachments_get_data: List of dictionaries containing the expected attachment data as would
            be required for an `AttachmentMetadataSchema`.
        """
        assert self._get_response_attachment.status_code == 200
        assert self._get_response_attachment.json() == expected_attachments_get_data

    def check_get_attachments_failed_with_message(self, status_code, expected_detail, obtained_detail):
        """Checks the response of listing attachments failed with the expected message."""

        assert self._get_response_attachment.status_code == status_code
        assert obtained_detail == expected_detail


class TestList(ListDSL):
    """Tests for getting a list of attachments."""

    def test_list_with_no_filters(self):
        """
        Test getting a list of all attachments with no filters provided.

        Posts three attachments and expects all of them to be returned.
        """

        attachments = self.post_test_attachments()
        self.get_attachments()
        self.check_get_attachments_success(attachments)

    def test_list_with_entity_id_filter(self):
        """
        Test getting a list of all attachments with an `entity_id` filter provided.

        Posts three attachments and then filter using the `entity_id`.
        """

        attachments = self.post_test_attachments()
        self.get_attachments(filters={"entity_id": attachments[0]["entity_id"]})
        self.check_get_attachments_success(attachments[:2])

    def test_list_with_entity_id_filter_with_no_matching_results(self):
        """
        Test getting a list of all attachments with an `entity_id` filter provided.

        Posts three attachments and expects no results.
        """

        self.post_test_attachments()
        self.get_attachments(filters={"entity_id": ObjectId()})
        self.check_get_attachments_success([])

    def test_list_with_invalid_entity_id_filter(self):
        """
        Test getting a list of all attachments with an invalid `entity_id` filter provided.

        Posts three attachments and expects a 422 status code.
        """

        self.post_test_attachments()
        self.get_attachments(filters={"entity_id": False})
        self.check_get_attachments_failed_with_message(
            422, "Invalid ID given", self._get_response_attachment.json()["detail"]
        )


class UpdateDSL(ListDSL):
    """Base class for update tests."""

    _patch_response_attachment: Response

    def patch_attachment(self, attachment_id: str, attachment_patch_data: dict) -> None:
        """
        Patches an attachment with the given ID.

        :param attachment_id: ID of the attachment to be updated.
        :param attachment_patch_data: Dictionary containing the attachment patch data as would be required for an
            `AttachmentPatchSchema`.
        """

        self._patch_response_attachment = self.test_client.patch(
            f"/attachments/{attachment_id}",
            json=attachment_patch_data,
        )

    def check_patch_attachment_success(self, expected_attachment_get_data: dict) -> None:
        """
        Checks that a prior call to `patch_attachment` gave a successful response with the expected data returned.

        :param expected_attachment_get_data: Dictionaries containing the expected attachment data as would be
            required for an `AttachmentMetadataSchema`.
        """

        assert self._patch_response_attachment.status_code == 200
        assert self._patch_response_attachment.json() == expected_attachment_get_data

    def check_patch_attachment_failed_with_detail(self, status_code: int, detail: str) -> None:
        """
        Checks that a prior call to `patch_attachment` gave a failed response with the expected code and detail.

        :param status_code: Expected status code to be returned.
        :param detail: Expected detail to be returned.
        """

        assert self._patch_response_attachment.status_code == status_code
        assert self._patch_response_attachment.json()["detail"] == detail


class TestUpdate(UpdateDSL):
    """Tests for updating an attachment."""

    def test_update_all_fields(self):
        """Test updating every field of an attachment."""

        attachment_id = self.post_attachment(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.patch_attachment(attachment_id, ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES)
        self.check_patch_attachment_success(ATTACHMENT_GET_METADATA_DATA_ALL_VALUES_AFTER_PATCH)

    def test_update_with_non_existent_id(self):
        """Test updating a non-existent attachment."""

        self.patch_attachment(str(ObjectId()), {})
        self.check_patch_attachment_failed_with_detail(404, "Attachment not found")

    def test_update_invalid_id(self):
        """Test updating an attachment with an invalid ID."""

        self.patch_attachment("invalid-id", {})
        self.check_patch_attachment_failed_with_detail(404, "Attachment not found")
