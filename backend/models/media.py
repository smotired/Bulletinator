"""Request and response models for media"""

from pydantic import BaseModel
from backend.models import shared

class Image(BaseModel):
    """Response model for images"""
    id: int
    filename: str
    
class ImageCollection(BaseModel):
    """Response models for image collections"""
    metadata: shared.Metadata
    images: list[Image]