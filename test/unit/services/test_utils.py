"""
Unit tests for the `utils` in /services.
"""

# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?

from object_storage_api.services import utils


class TestGenerateCode:
    """Tests for the `generate_code` method"""

    def test_generate_code(self):
        """Test `generate_code` works correctly"""

        result = utils.generate_code("string with spaces", "entity_type")
        assert result == "string-with-spaces"
