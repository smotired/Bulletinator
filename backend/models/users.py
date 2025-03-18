"""Request and response models for user functionality"""

from pydantic import BaseModel
from typing import Annotated
from fastapi import Form

from backend.models import media, shared

class User(BaseModel):
    """Response model for users"""
    id: int
    username: str
    profile_image: media.Image | None = None
    
class UserCollection(BaseModel):
    """Response model for a collection of users"""
    metadata: shared.Metadata
    users: list[User]
    
class UserUpdate(BaseModel):
    """Request model to update an account."""
    old_password: str | None = None # not necessary unless updating email or password
    
    username: str | None = None
    profile_image_filename: str | None = None # requires uploading the image beforehand
    email: str | None = None
    new_password: str | None = None
    
UserUpdateForm = Annotated[UserUpdate, Form()]