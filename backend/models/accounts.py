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
    
class AuthenticatedAccount(BaseModel):
    """Response model for authenticated accounts which provides more information"""
    id: str
    username: str
    email: str
    profile_image: str | None = None
    
class AccountCollection(BaseModel):
    """Response model for a collection of accounts"""
    metadata: shared.Metadata
    accounts: list[Account]
    
class AccountUpdate(BaseModel):
    """Request model to update an account."""
    old_password: str | None = None # not necessary unless updating email or password
    
    username: str | None = None
    profile_image: str | None = None # requires uploading the image beforehand
    email: str | None = None
    new_password: str | None = None
    
AccountUpdateForm = Annotated[AccountUpdate, Form()]

def convert_account(db_account: DBAccount):
    return Account.model_validate(db_account.__dict__)

def convert_auth_account(db_account: DBAccount):
    return AuthenticatedAccount.model_validate(db_account.__dict__)

def convert_account_list(db_accounts: list[DBAccount]):
    return [ convert_account(db_account) for db_account in db_accounts ]