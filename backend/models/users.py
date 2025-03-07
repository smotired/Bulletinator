"""Request and response models for user functionality"""

from pydantic import BaseModel
from typing import Annotated
from fastapi import Form

import media
import shared

class User(BaseModel):
    """Response model for users"""
    id: int
    username: str
    profile_image: media.Image
    
class UserCollection(BaseModel):
    """Response model for a collection of users"""
    metadata: shared.Metadata
    users: list[User]
    
class UserUpdate(BaseModel):
    """Request model to update an account."""
    username: str | None = None
    profile_image_filename: str | None = None # requires uploading the image beforehand
    
class PasswordUpdate(BaseModel):
    """Request model to update sensitive account information"""
    old_password: str | None = None
    
    email: str | None = None
    new_password: str | None = None
    
PasswordUpdateForm = Annotated[PasswordUpdate, Form()]