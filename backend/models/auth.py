"""Request and response models for authentication functionality"""

from pydantic import BaseModel
    
class Registration(BaseModel):
    """Request model for registering an account"""
    username: str
    email: str
    password: str
    
class Login(BaseModel):
    """Request model for logging in an account with email or password"""
    identifier: str
    password: str

class PasswordChange(BaseModel):
    """Request model for changing a password"""
    password: str
    confirm_password: str
    
class AccessToken(BaseModel):
    """Response model for a JWT request"""
    access_token: str
    token_type: str
    
class AccessPayload(BaseModel):
    """Model for JWT access token payload"""
    sub: str # subject. account ID as string
    iss: str # issuer domain
    iat: int # time this token was issued
    exp: int # time after which this token has expired
    
class RefreshPayload(BaseModel):
    """Model for JWT refresh token payload"""
    sub: str # subject. account ID as string.
    uid: str # unique ID of this token so we can manually revoke it
    iss: str # issuer domain
    iat: int # time this token was issued
    exp: int # time after which this token has expired