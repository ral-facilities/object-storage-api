"""
Module for providing common test configuration, test fixtures, and helper functions.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

MODEL_MIXINS_FIXED_DATETIME_NOW = datetime(2024, 2, 16, 14, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(name="model_mixins_datetime_now_mock")
def fixture_model_mixins_datetime_now_mock():
    """
    Fixture that mocks the `datetime.now` method in the `inventory_management_system_api.models.mixins` module.
    """
    with patch("object_storage_api.models.mixins.datetime") as mock_datetime:
        mock_datetime.now.return_value = MODEL_MIXINS_FIXED_DATETIME_NOW
        yield mock_datetime
