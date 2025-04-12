"""Request and response models for user functionality"""

from pydantic import BaseModel
from typing import Annotated
from fastapi import Form
from backend.database.schema import DBUser

from backend.models import  shared

class User(BaseModel):
    """Response model for users"""
    id: int
    username: str
    profile_image: str | None = None
    
class AuthenticatedUser(BaseModel):
    """Response model for authenticated users which provides more information"""
    id: int
    username: str
    email: str
    profile_image: str | None = None
    
class UserCollection(BaseModel):
    """Response model for a collection of users"""
    metadata: shared.Metadata
    users: list[User]
    
class UserUpdate(BaseModel):
    """Request model to update an account."""
    old_password: str | None = None # not necessary unless updating email or password
    
    username: str | None = None
    profile_image: str | None = None # requires uploading the image beforehand
    email: str | None = None
    new_password: str | None = None
    
UserUpdateForm = Annotated[UserUpdate, Form()]

def convert_user(db_user: DBUser):
    return User.model_validate(db_user.__dict__)

def convert_auth_user(db_user: DBUser):
    return AuthenticatedUser.model_validate(db_user.__dict__)

def convert_user_list(db_users: list[DBUser]):
    return [ convert_user(db_user) for db_user in db_users ]