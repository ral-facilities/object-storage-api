"""
Module for the overall configuration for the application.
"""

from pathlib import Path
from typing import List

from pydantic import BaseModel, ConfigDict, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIConfig(BaseModel):
    """
    Configuration model for the API.
    """

    title: str = "Object Storage Service API"
    description: str = "This is the API for the Object Storage Service"
    root_path: str = ""  # (If using a proxy) The path prefix handled by a proxy that is not seen by the app.
    allowed_cors_headers: List[str]
    allowed_cors_origins: List[str]
    allowed_cors_methods: List[str]


class DatabaseConfig(BaseModel):
    """
    Configuration model for the database.
    """

    protocol: SecretStr
    username: SecretStr
    password: SecretStr
    host_and_options: SecretStr
    name: SecretStr

    model_config = ConfigDict(hide_input_in_errors=True)


class ObjectStorageConfig(BaseModel):
    """
    Configuration model for the S3 object storage.
    """

    endpoint_url: SecretStr
    access_key: SecretStr
    secret_access_key: SecretStr
    bucket_name: SecretStr
    presigned_url_expiry_seconds: int

    model_config = ConfigDict(hide_input_in_errors=True)


class AttachmentConfig(BaseModel):
    """
    Configuration model for attachments.
    """

    max_size_bytes: int


class ImageConfig(BaseModel):
    """
    Configuration model for images.
    """

    thumbnail_max_size_pixels: int


class Config(BaseSettings):
    """
    Overall configuration model for the application.

    It includes attributes for the API, authentication, database, and object storage configurations. The class
    inherits from `BaseSettings` and automatically reads environment variables. If values are not passed in form of
    system environment variables at runtime, it will attempt to read them from the .env file.
    """

    api: APIConfig
    database: DatabaseConfig
    object_storage: ObjectStorageConfig
    attachment: AttachmentConfig
    image: ImageConfig

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        hide_input_in_errors=True,
    )


config = Config()
