"""
End-to-End tests for the attachment router.
"""

from test.mock_data import (
    ATTACHMENT_GET_DATA_ALL_VALUES,
    ATTACHMENT_GET_METADATA_ALL_VALUES,
    ATTACHMENT_GET_METADATA_DATA_ALL_VALUES_AFTER_PATCH,
    ATTACHMENT_GET_METADATA_REQUIRED_VALUES_ONLY,
    ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES,
    ATTACHMENT_POST_DATA_ALL_VALUES,
    ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY,
    ATTACHMENT_POST_RESPONSE_DATA_ALL_VALUES,
    ATTACHMENT_POST_RESPONSE_DATA_REQUIRED_VALUES_ONLY,
)
from typing import Optional

import pytest
import requests
from bson import ObjectId
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
        :return: ID of the created attachment (or `None` if unsuccessful).
        """

        self._post_response_attachment = self.test_client.post("/attachments", json=attachment_post_data)
        return (
            self._post_response_attachment.json()["id"] if self._post_response_attachment.status_code == 201 else None
        )

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
            {**ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY, "entity_id": entity_id_a},
        )

        # Second item
        attachment_b_id = self.post_attachment(
            {**ATTACHMENT_POST_DATA_ALL_VALUES, "entity_id": entity_id_a},
        )

        # Third item
        attachment_c_id = self.post_attachment(
            {**ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY, "entity_id": entity_id_b},
        )

        return [
            {
                **ATTACHMENT_GET_METADATA_REQUIRED_VALUES_ONLY,
                "entity_id": entity_id_a,
                "id": attachment_a_id,
            },
            {
                **ATTACHMENT_GET_METADATA_ALL_VALUES,
                "entity_id": entity_id_a,
                "id": attachment_b_id,
            },
            {
                **ATTACHMENT_GET_METADATA_REQUIRED_VALUES_ONLY,
                "entity_id": entity_id_b,
                "id": attachment_c_id,
            },
        ]

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

    def test_create_with_unsupported_file_extension(self):
        """Test creating an attachment with an unsupported file extension."""

        self.post_attachment({**ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY, "file_name": "test.html"})
        self.check_post_attachment_failed_with_detail(415, "File extension is not supported")

    def test_create_when_upload_limit_reached(self):
        """
        Test creating an attachment when the upload limit has been reached.
        """

        attachments = self.post_test_attachments()

        self.post_attachment({**ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY, "entity_id": attachments[0]["entity_id"]})
        self.check_post_attachment_failed_with_detail(
            422, "Limit for the maximum number of attachments for the provided `entity_id` has been reached"
        )

    def test_create_with_duplicate_file_name_within_parent(self):
        """Test creating an attachment with the same name as another within the parent entity."""

        self.post_attachment(ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY)
        self.post_attachment(ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY)
        self.check_post_attachment_failed_with_detail(
            409, "An attachment with the same file name already exists within the parent entity."
        )


class GetDSL(CreateDSL):
    """Base class for get tests."""

    _get_response_attachment: Response

    def get_attachment(self, attachment_id: str) -> None:
        """
        Gets an attachment with the given ID.

        :param attachment_id: The ID of the attachment to be obtained.
        """
        self._get_response_attachment = self.test_client.get(f"/attachments/{attachment_id}")

    def check_get_attachment_success(self, expected_attachment_data: dict) -> None:
        """
        Checks that a prior call to `get_attachment` gave a successful response with the expected data returned.

        :param expected_attachment_data: Dictionary containing the expected attachment data as would be required
            for an `AttachmentMetadataSchema`.
        """
        assert self._get_response_attachment.status_code == 200
        assert self._get_response_attachment.json() == expected_attachment_data

    def check_get_attachment_failed_with_detail(self, status_code: int, detail: str) -> None:
        """
        Checks that a prior call to `get_attachment` gave a failed response with the expected code and error message.

        :param status_code: Expected status code of the response.
        :param detail: Expected error message given in the response.
        """
        assert self._get_response_attachment.status_code == status_code
        assert self._get_response_attachment.json()["detail"] == detail


class TestGet(GetDSL):
    """Tests for getting an attachment."""

    def test_get_with_valid_attachment_id(self):
        """Test getting an attachment with a valid attachment ID."""
        attachment_id = self.post_attachment(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.get_attachment(attachment_id)
        self.check_get_attachment_success(ATTACHMENT_GET_DATA_ALL_VALUES)

    def test_get_with_invalid_attachment_id(self):
        """Test getting an attachment with an invalid attachment ID."""
        self.get_attachment("ababababab")
        self.check_get_attachment_failed_with_detail(404, "Attachment not found")

    def test_get_with_non_existent_attachment_id(self):
        """Test getting an attachment with a non-existent attachment ID."""
        attachment_id = str(ObjectId())
        self.get_attachment(attachment_id)
        self.check_get_attachment_failed_with_detail(404, "Attachment not found")


class ListDSL(GetDSL):
    """Base class for list tests."""

    def get_attachments(self, filters: Optional[dict] = None) -> None:
        """
        Gets a list of attachments with the given filters.

        :param filters: Filters to use in the request.
        """
        self._get_response_attachment = self.test_client.get("/attachments", params=filters)

    def check_get_attachments_success(self, expected_attachments_get_data: list[dict]) -> None:
        """
        Checks that a prior call to `get_attachments` gave a successful response with the expected data returned.

        :param expected_attachments_get_data: List of dictionaries containing the expected attachment data as would
            be required for an `AttachmentMetadataSchema`.
        """
        assert self._get_response_attachment.status_code == 200
        assert self._get_response_attachment.json() == expected_attachments_get_data


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

        Posts three attachments and expects no results.
        """

        self.post_test_attachments()
        self.get_attachments(filters={"entity_id": False})
        self.check_get_attachments_success([])


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

    def test_partial_update_with_file_extension_content_type_mismatch(self):
        """Test updating an attachment with a different extension."""
        attachment_id = self.post_attachment(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.patch_attachment(attachment_id, {**ATTACHMENT_PATCH_METADATA_DATA_ALL_VALUES, "file_name": "report.mp3"})
        self.check_patch_attachment_failed_with_detail(422, "File extension and content type do not match")

    def test_update_file_name_to_duplicate(self):
        """Test updating the name of an attachment to conflict with a pre-existing one."""

        self.post_attachment({**ATTACHMENT_POST_DATA_ALL_VALUES, "file_name": "test.pdf"})
        attachment_id = self.post_attachment(ATTACHMENT_POST_DATA_ALL_VALUES)
        self.patch_attachment(attachment_id, {"file_name": "test.pdf"})
        self.check_patch_attachment_failed_with_detail(
            409, "An attachment with the same file name already exists within the parent entity."
        )


class DeleteDSL(ListDSL):
    """Base class for delete tests."""

    _delete_response_attachment: Response

    def delete_attachment(self, attachment_id: str) -> None:
        """
        Deletes an attachment with the given ID.
        :param attachment_id: ID of the attachment to be deleted.
        """
        self._delete_response_attachment = self.test_client.delete(f"/attachments/{attachment_id}")

    def check_delete_attachment_success(self) -> None:
        """Checks that a prior call to `delete_attachment` gave a successful response with the expected code."""
        assert self._delete_response_attachment.status_code == 204

    def check_delete_attachment_failed_with_detail(self, status_code: int, detail: str) -> None:
        """
        Checks that a prior call to `delete_attachment` gave a failed response with the expected code and
        error message.

        :param status_code: Expected status code of the response.
        :param detail: Expected error message given in the response.
        """
        assert self._delete_response_attachment.status_code == status_code
        assert self._delete_response_attachment.json()["detail"] == detail


class TestDelete(DeleteDSL):
    """Tests for deleting an attachment."""

    def test_delete(self):
        """Test deleting an attachment."""
        attachment_id = self.post_attachment(ATTACHMENT_POST_DATA_REQUIRED_VALUES_ONLY)

        self.delete_attachment(attachment_id)
        self.check_delete_attachment_success()

        self.get_attachment(attachment_id)
        self.check_get_attachment_failed_with_detail(404, "Attachment not found")

    def test_delete_with_non_existent_id(self):
        """Test deleting a non-existent attachment."""
        self.delete_attachment(str(ObjectId()))
        self.check_delete_attachment_failed_with_detail(404, "Attachment not found")

    def test_delete_with_invalid_id(self):
        """Test deleting an attachment with an invalid ID."""
        self.delete_attachment("invalid_id")
        self.check_delete_attachment_failed_with_detail(404, "Attachment not found")


class DeleteByEntityIdDSL(ListDSL):
    """Base class for delete by `entity_id` tests."""

    _delete_response_attachments: Response

    def delete_attachments_by_entity_id(self, entity_id: str) -> None:
        """
        Deletes attachments with the given `entity_id`.

        :param entity_id: Entity ID of the attachments to be deleted.
        """
        self._delete_response_attachments = self.test_client.delete("/attachments", params={"entity_id": entity_id})

    def check_delete_attachments_by_entity_id_success(self) -> None:
        """
        Checks that a prior call to `delete_attachments_by_entity_id` gave a successful response with the expected code.
        """
        assert self._delete_response_attachments.status_code == 204


class TestDeleteByEntityId(DeleteByEntityIdDSL):
    """Tests for deleting attachments by `entity_id`."""

    def test_delete_by_entity_id(self):
        """Test deleting attachments."""
        attachments = self.post_test_attachments()
        entity_id = attachments[0]["entity_id"]

        self.delete_attachments_by_entity_id(entity_id)
        self.check_delete_attachments_by_entity_id_success()

        self.get_attachments(filters={"entity_id": entity_id})
        self.check_get_attachments_success([])

    def test_delete_by_entity_id_with_non_existent_id(self):
        """Test deleting attachments with a non-existent `entity_id`."""
        self.delete_attachments_by_entity_id(str(ObjectId()))
        self.check_delete_attachments_by_entity_id_success()

    def test_delete_by_entity_id_with_invalid_id(self):
        """Test deleting attachments with an invalid `entity_id`."""
        self.delete_attachments_by_entity_id("invalid_id")
        self.check_delete_attachments_by_entity_id_success()
