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
        self.message = "Authentication failed: invalid credentials"
        
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

class InvalidEmailVerification(BadRequestException):
    def __init__(self):
        self.status_code = 401
        self.error = "invalid_email_verification"
        self.message = "Could not verify email address"
        
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

class NoPermissions(BadRequestException):
    def __init__(self, action: str, entity: str, id: str):
        self.status_code = 403
        self.error = "no_permissions"
        self.message = f"No permissions to {action} on {entity} with id={id}"

class UnverifiedEmailAddress(BadRequestException):
    def __init__(self):
        self.status_code = 403
        self.error = "unverified_email_address"
        self.message = "This action requires a verified email address"

class ItemTypeMismatch(BadRequestException):
    def __init__(self, id: str, expected: str, actual: str):
        self.status_code = 418
        self.error = "item_type_mismatch"
        self.message = f"Item with id={id} has type '{actual}', but was treated as if it had type '{expected}'"

class InvalidOperation(BadRequestException):
    def __init__(self, message: str):
        self.status_code = 422
        self.error = "invalid_operation"
        self.message = message

class AddBoardOwnerAsEditor(BadRequestException):
    def __init__(self):
        self.status_code = 422
        self.error = "add_board_owner_as_editor"
        self.message = "Cannot add the board owner as an editor"

class InvalidItemType(BadRequestException):
    def __init__(self, type: str):
        self.status_code = 422
        self.error = "invalid_item_type"
        self.message = f"Item type '{type}' is not valid"

class MissingItemFields(BadRequestException):
    def __init__(self, type: str, fields: list[str]):
        self.status_code = 422
        self.error = "missing_item_fields"
        self.message = f"Item type '{type}' was missing the following fields: {fields}"

class IndexOutOfRange(BadRequestException):
    def __init__(self, entity: str, id:str, index: str):
        self.status_code = 422
        self.error = "out_of_range"
        self.message = f"Index {index} out of range for {entity} with id={id}"

class AddListToList(BadRequestException):
    def __init__(self):
        self.status_code = 422
        self.error = "add_list_to_list"
        self.message = "Cannot add a list to another list"

class UnsupportedFileType(BadRequestException):
    def __init__(self, type: str, target: str):
        self.status_code = 422
        self.error = "unsupported_file_type"
        self.message = f"File type '{type}' is not a supported type of {target}"

class FileTooLarge(BadRequestException):
    def __init__(self, entity: str, limit_str: str):
        self.status_code = 422
        self.error = "file_too_large"
        self.message = f"Files of type '{entity}' must be no larger than {limit_str}"

class InvalidField(BadRequestException):
    def __init__(self, value: str, field: str):
        self.status_code = 422
        self.error = "invalid_field"
        self.message = f"Value '{value}' is invalid for field '{field}'"

class FieldTooLong(BadRequestException):
    def __init__(self, field: str):
        self.status_code = 422
        self.error = "field_too_long"
        self.message = f"Input to field '{field}' exceeded the maximum length"

class WebhookError(BadRequestException):
    def __init__(self, detail: str):
        self.status_code = 422
        self.error = "webhook_error"
        self.message = f"The webhook payload had an invalid format or signature: {detail}"

class TooManyRequests(BadRequestException):
    def __init__(self):
        self.status_code = 429
        self.error = "too_many_requests"
        self.message = f"You are accessing this resource too quickly. Please try again later."