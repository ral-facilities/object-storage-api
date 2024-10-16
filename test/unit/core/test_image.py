"""
Unit tests for image processing functions.
"""

import pytest
from fastapi import UploadFile

from object_storage_api.core.exceptions import InvalidImageFileError
from object_storage_api.core.image import generate_thumbnail_base64_str


class TestGenerateThumbnailBase64Str:
    """Tests for the `generate_thumbnail_base64_str` method."""

    def test_with_valid_image(self):
        """Tests `generate_thumbnail_base64_str` with a valid image file provided."""

        with open("test/files/image.jpg", "rb") as file:
            uploaded_image_file = UploadFile(file, filename="image.jpg")
            result = generate_thumbnail_base64_str(uploaded_image_file)

        assert result == "UklGRjQAAABXRUJQVlA4ICgAAADQAQCdASoCAAEAAUAmJYwCdAEO/gOOAAD+qlQWHDxhNJOjVlqIb8AA"

    def test_with_invalid_image(self):
        """Tests `generate_thumbnail_base64_str` with an invalid image file provided."""

        with open("test/files/invalid_image.jpg", "rb") as file:
            uploaded_image_file = UploadFile(file, filename="image.jpg")
            with pytest.raises(InvalidImageFileError) as exc:
                generate_thumbnail_base64_str(uploaded_image_file)

            assert str(exc.value) == f"The uploaded file '{uploaded_image_file.filename}' could not be opened by Pillow"
