"""Exceptions module.

Custom exceptions that can be raised anywhere in the application
- Any child exception of BadRequestException is handled to return a JSON response

This was part of the backend project for my CS 4550 class, courtesy of Aaron Wood

Examples:
- Building a child exception
  ```python
  class MyCustomException(BadRequestException):
      def __init__(self, *args, **kwargs):
          self.status_code = 400
          self.error = "my_error_code"
          self.message = "My error message"
  ```
  and raising `MyCustomException()` will render a JSON response with the specified status
  code and the response body
  ```json
  {
    "error": "my_error_code",
    "message": "My error message",
  }
  ```

- Alternatively
  ```python
  raise BadRequestException(
      status_code=400,
      error="my_error_code",
      message="My error message",
  )
  ```
  will render the same JSON response as above.
"""

from typing import Any
from fastapi.responses import JSONResponse, Response
from backend.models.shared import BadRequest

class BadRequestException(Exception):
    """General purpose class for 400 exceptions.

    Args:
        status_code (int): The HTTP status code; defaults to 400
        error (str): The error code
        message (str): The error message
    """

    def __init__(self, *, status_code: int = 400, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message

    def response_content(self) -> BadRequest:
        return BadRequest(error=self.error, message=self.message)

    def response(self) -> Response:
        """Build a JSON response for the exception."""

        return JSONResponse(
            status_code=self.status_code,
            content=self.response_content().model_dump(),
        )
        
# Exceptions

class EntityNotFound(BadRequestException):
    def __init__(self, entity: str, property: str, value: Any):
        self.status_code = 404
        self.error = "entity_not_found"
        self.message = f"Unable to find {entity} with {property}={value}"
        
class DuplicateEntity(BadRequestException):
    def __init__(self, entity: str, field_name: str, field_value: Any):
        self.status_code = 422
        self.error = "duplicate_entity"
        self.message = f"Entity {entity} with {field_name}={field_value} already exists"
        
class InvalidCredentials(BadRequestException):
    def __init__(self):
        self.status_code = 401
        self.error = "invalid_credentials"
        self.message = "Authentication failed: invalid username or password"
        
class InvalidAccessToken(BadRequestException):
    def __init__(self):
        self.status_code = 401
        self.error = "invalid_access_token"
        self.message = "Authentication failed: Access token expired or was invalid"
        
class InvalidRefreshToken(BadRequestException):
    def __init__(self):
        self.status_code = 401
        self.error = "invalid_refresh_token"
        self.message = "Authentication failed: Refresh token expired or was invalid"
        
class NotAuthenticated(BadRequestException):
    def __init__(self):
        self.status_code = 403
        self.error = "not_authenticated"
        self.message = "Not authenticated"

class AccessDenied(BadRequestException):
    def __init__(self):
        self.status_code = 403
        self.error = "access_denied"
        self.message = "Access denied"