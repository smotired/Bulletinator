"""Request and response models for authentication functionality"""

from pydantic import BaseModel
from typing import Annotated, Union
from fastapi import Form

import media
    
class AuthenticatedUser(BaseModel):
    """Response model for authenticated users which provides more information"""
    id: int
    username: str
    email: str
    profile_image: media.Image
    
class Registration(BaseModel):
    """Request model for registering a user"""
    username: str
    email: str
    password: str

RegistrationForm = Annotated[Registration, Form()]
    
class LoginUsername(BaseModel):
    """Request model for logging in a user with the usename"""
    username: str
    password: str
    
class LoginEmail(BaseModel):
    """Request model for logging in a user with the email"""
    email: str
    password: str
    
Login = Union[LoginEmail, LoginUsername]
LoginForm = Annotated[Login, Form()]
    
class AccessToken(BaseModel):
    """Response model for a JWT request"""
    access_token: str
    token_type: str
    
class AccessPayload(BaseModel):
    """Model for JWT access token payload"""
    sub: str # subject. user ID as string
    iss: str # issuer domain
    iat: int # time this token was issued
    exp: int # time after which this token has expired
    
class RefreshPayload(BaseModel):
    """Model for JWT refresh token payload"""
    sub: str # subject. user ID as string.
    uid: str # unique ID of this token so we can manually revoke it
    iss: str # issuer domain
    iat: int # time this token was issued
    exp: int # time after which this token has expired