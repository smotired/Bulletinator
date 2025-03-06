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
from pydantic import BaseModel

class BadRequest(BaseModel):
    """Response model for error messages."""
    
    error: str
    message: str

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