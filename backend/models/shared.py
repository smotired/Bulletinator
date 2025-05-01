"""Request and response models for shared functionality."""

from pydantic import BaseModel

class BadRequest(BaseModel):
    """Response model for error messages."""
    
    error: str
    message: str
    
class Metadata(BaseModel):
    """Used in response models for collections. May have more fields later."""

    count: int

class Success(BaseModel):
    """Response model for a very basic success."""
    status: str = "success"