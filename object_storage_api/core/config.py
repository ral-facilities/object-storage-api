"""
Module for the overall configuration for the application.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationInfo, field_validator
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


# pylint:disable=fixme
# TODO: Some of this file is identical to the one in inventory-management-system-api - Use common repo?


class AuthenticationConfig(BaseModel):
    """
    Configuration model for the JWT access token authentication/authorization.
    """

    enabled: bool
    public_key_path: Optional[str] = Field(default=None, validate_default=True)
    jwt_algorithm: Optional[str] = Field(default=None, validate_default=True)

    @field_validator("public_key_path", "jwt_algorithm")
    @classmethod
    def validate_optional_fields(cls, field_value: str, info: ValidationInfo) -> Optional[str]:
        """
        Validator for the `public_key_path` and `jwt_algorithm` fields to make them mandatory if the value of the
        `enabled` is `True`

        It checks if the `enabled` field has been set to `True` and raises a `TypeError` if this is the case.

        :param field_value: The value of the field.
        :param info: Validation info from pydantic.
        :raises ValueError: If no value is provided for the field when `enabled` is set to `True`.
        :return: The value of the field.
        """
        if ("enabled" in info.data and info.data["enabled"] is True) and field_value is None:
            raise ValueError("Field required")
        return field_value


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

    allowed_file_extensions: list[str]
    thumbnail_max_size_pixels: int


class Config(BaseSettings):
    """
    Overall configuration model for the application.

    It includes attributes for the API, authentication, database, and object storage configurations. The class
    inherits from `BaseSettings` and automatically reads environment variables. If values are not passed in form of
    system environment variables at runtime, it will attempt to read them from the .env file.
    """

    api: APIConfig
    authentication: AuthenticationConfig
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
