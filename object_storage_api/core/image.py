"""
Module for processing images.
"""

import base64
import logging
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from object_storage_api.core.config import config
from object_storage_api.core.exceptions import InvalidImageFileError

logger = logging.getLogger()

image_config = config.image


def generate_thumbnail_base64_str(uploaded_image_file: UploadFile) -> str:
    """
    Generates a thumbnail from an uploaded image file.

    :param uploaded_image_file: Uploaded image file.
    :return: Base64 encoded string of the thumbnail
    :raises: InvalidImageFileError if the given image file cannot be processed due to being invalid in some way.
    """

    logger.debug("Generating thumbnail for uploaded image file")

    # Image may fail to open if the file is either not an image or is invalid in some other way
    try:
        pillow_image = Image.open(uploaded_image_file.file)
    except UnidentifiedImageError as exc:
        raise InvalidImageFileError(
            f"The uploaded file '{uploaded_image_file.filename}' could not be opened by Pillow"
        ) from exc

    pillow_image.thumbnail(
        (image_config.thumbnail_max_size_pixels, image_config.thumbnail_max_size_pixels),
        # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters-comparison-table
        resample=Image.Resampling.BICUBIC,
    )

    # Save into memory buffer using the WebP image format (There are other options available at
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp)
    memory_image_buffer = BytesIO()
    pillow_image.save(memory_image_buffer, "webp")

    # Move buffer back to start ready for reading (it will be at the end after generating the thumbnail)
    uploaded_image_file.file.seek(0)

    # Encode the thumbnail data into a UTF-8 encoded bytestring
    return base64.b64encode(memory_image_buffer.getvalue()).decode("utf-8")
