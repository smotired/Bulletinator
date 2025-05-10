"""Request and response models for media"""

from pydantic import BaseModel
from backend.models import shared

class Image(BaseModel):
    """Response model for images"""
    uuid: str
    filename: str