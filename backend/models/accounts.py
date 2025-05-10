"""Request and response models for account functionality"""

from pydantic import BaseModel
from typing import Annotated
from fastapi import Form
from backend.database.schema import DBAccount

from backend.models import  shared

class Account(BaseModel):
    """Response model for accounts"""
    id: str
    username: str
    profile_image: str | None = None
    display_name: str | None = None
    
class AuthenticatedAccount(BaseModel):
    """Response model for authenticated accounts which provides more information"""
    id: str
    username: str
    email: str | None = None
    profile_image: str | None = None
    display_name: str | None = None
    
class AccountUpdate(BaseModel):
    """Request model to update an account."""
    old_password: str | None = None # not necessary unless updating email or password
    
    username: str | None = None
    profile_image: str | None = None # requires uploading the image beforehand
    display_name: str | None = None # set to the empty string to reset to none
    email: str | None = None
    new_password: str | None = None
    
AccountUpdateForm = Annotated[AccountUpdate, Form()]