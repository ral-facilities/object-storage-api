"""
Module for providing an implementation of the `JWTBearer` class.
"""

import logging

import jwt
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from object_storage_api.core.config import config
from object_storage_api.core.consts import PUBLIC_KEY

# pylint:disable=fixme
# TODO: This file is identical to the one in inventory-management-system-api - Use common repo?


logger = logging.getLogger()

security = HTTPBearer(auto_error=True)


class JWTMiddleware(BaseHTTPMiddleware):
    """
    A middleware class to provide JSON Web Token (JWT) based authentication/authorization.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Performs JWT access token authentication/authorization before processing the request.

        :param request: The Starlette `Request` object.
        :param call_next: The next function to call to process the `Request` object.
        :return: The JWT access token if authentication is successful.
        :raises HTTPException: If the supplied JWT access token is invalid or has expired.
        """
        if (
            not request.url.path == f"{config.api.root_path}/docs"
            and not request.url.path == f"{config.api.root_path}/openapi.json"
        ):
            try:
                credentials: HTTPAuthorizationCredentials = await security(request)
            except HTTPException as exc:
                # Cannot raise HttpException here, so must do manually
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

            if not self._is_jwt_access_token_valid(credentials.credentials):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Invalid token or expired token"}
                )

        return await call_next(request)

    def _is_jwt_access_token_valid(self, access_token: str) -> bool:
        """
        Check if the JWT access token is valid.

        It does this by checking that it was signed by the corresponding private key and has not expired. It also
        requires the payload to contain a username.
        :param access_token: The JWT access token to check.
        :return: `True` if the JWT access token is valid and its payload contains a username, `False` otherwise.
        """
        logger.info("Checking if JWT access token is valid")
        try:
            payload = jwt.decode(access_token, PUBLIC_KEY, algorithms=[config.authentication.jwt_algorithm])
        except Exception:  # pylint: disable=broad-exception-caught)
            logger.exception("Error decoding JWT access token")
            payload = None

        return payload is not None and "username" in payload
