"""
Module for providing common test configuration and test fixtures.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from object_storage_api.repositories.attachment import AttachmentRepo
from object_storage_api.repositories.image import ImageRepo
from object_storage_api.services.attachment import AttachmentService
from object_storage_api.services.image import ImageService
from object_storage_api.stores.attachment import AttachmentStore
from object_storage_api.stores.image import ImageStore


@pytest.fixture(name="attachment_repository_mock")
def fixture_attachment_repository_mock() -> Mock:
    """
    Fixture to create a mock of the `AttachmentRepo` dependency.

    :return: Mocked `AttachmentRepo` instance.
    """
    return Mock(AttachmentRepo)


@pytest.fixture(name="image_repository_mock")
def fixture_image_repository_mock() -> Mock:
    """
    Fixture to create a mock of the `ImageRepo` dependency.

    :return: Mocked `ImageRepo` instance.
    """
    return Mock(ImageRepo)


@pytest.fixture(name="attachment_store_mock")
def fixture_attachment_store_mock() -> Mock:
    """
    Fixture to create a mock of the `AttachmentStore` dependency.

    :return: Mocked `AttachmentStore` instance.
    """
    return Mock(AttachmentStore)


@pytest.fixture(name="image_store_mock")
def fixture_image_store_mock() -> Mock:
    """
    Fixture to create a mock of the `ImageStore` dependency.

    :return: Mocked `ImageStore` instance.
    """
    return Mock(ImageStore)


@pytest.fixture(name="attachment_service")
def fixture_attachment_service(attachment_repository_mock: Mock, attachment_store_mock: Mock) -> AttachmentService:
    """
    Fixture to create a `AttachmentService` instance with mocked `AttachmentRepo` and `AttachmentStore` dependencies.

    :param attachment_repository_mock: Mocked `AttachmentRepo` instance.
    :param attachment_store_mock: Mocked `AttachmentStore` instance.
    :return: `AttachmentService` instance with the mocked dependencies.
    """
    return AttachmentService(attachment_repository_mock, attachment_store_mock)


@pytest.fixture(name="image_service")
def fixture_image_service(image_repository_mock: Mock, image_store_mock: Mock) -> AttachmentService:
    """
    Fixture to create a `ImageService` instance with mocked `ImageRepo` and `ImageStore` dependencies.

    :param image_repository_mock: Mocked `ImageRepo` instance.
    :param image_store_mock: Mocked `ImageStore` instance.
    :return: `ImageService` instance with the mocked dependencies.
    """
    return ImageService(image_repository_mock, image_store_mock)


MODEL_MIXINS_FIXED_DATETIME_NOW = datetime(2024, 2, 16, 14, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(name="model_mixins_datetime_now_mock")
def fixture_model_mixins_datetime_now_mock():
    """
    Fixture that mocks the `datetime.now` method in the `object_storage_api.models.mixins` module.
    """
    with patch("object_storage_api.models.mixins.datetime") as mock_datetime:
        mock_datetime.now.return_value = MODEL_MIXINS_FIXED_DATETIME_NOW
        yield mock_datetime
