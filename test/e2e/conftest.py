"""
Module providing test fixtures for the e2e tests.
"""

import pytest
from fastapi.testclient import TestClient

from object_storage_api.core.database import get_database
from object_storage_api.core.object_store import object_storage_config, s3_client
from object_storage_api.main import app


@pytest.fixture(name="test_client")
def fixture_test_client() -> TestClient:
    """
    Fixture for creating a test client for the application.

    :return: The test client.
    """
    return TestClient(app)


@pytest.fixture(name="cleanup_database_collections", autouse=True)
def fixture_cleanup_database_collections():
    """
    Fixture to clean up the collections in the test database after the session finishes.
    """
    database = get_database()
    yield
    database.attachments.delete_many({})
    database.images.delete_many({})


@pytest.fixture(name="cleanup_object_storage_bucket", autouse=True)
def fixture_cleanup_object_storage_bucket():
    """
    Fixture to clean up the test object storage bucket after session finishes.
    """
    yield
    objects = s3_client.list_objects_v2(Bucket=object_storage_config.bucket_name.get_secret_value())
    # If nothing uploaded there is no contents (Could happen if there are errors or if a test doesn't upload anything)
    if "Contents" in objects:
        objects = list(map(lambda x: {"Key": x["Key"]}, objects["Contents"]))
        s3_client.delete_objects(
            Bucket=object_storage_config.bucket_name.get_secret_value(), Delete={"Objects": objects}
        )
