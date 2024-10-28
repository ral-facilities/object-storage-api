"""
Contains constants used in multiple places so they are easier to change
"""

# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?

import sys

from object_storage_api.core.config import config

if config.authentication.enabled:
    # Read the content of the public key file into a constant. This is used for decoding of JWT access tokens.
    try:
        with open(config.authentication.public_key_path, "r", encoding="utf-8") as file:
            PUBLIC_KEY = file.read()
    except FileNotFoundError as exc:
        sys.exit(f"Cannot find public key: {exc}")
