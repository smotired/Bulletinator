"""Request and response models for authentication functionality"""

from pydantic import BaseModel
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
    
class Login(BaseModel):
    """Request model for logging in a user"""
    username: str
    password: str
    
# TODO: Figure out access and refresh tokens
class AccessToken(BaseModel):
    """Response model for a JWT request"""
    access_token: str
    token_type: str
    
class Claims(BaseModel):
    """Model for JWT access token payload"""
    sub: str # subject. user ID as string
    iss: str # issuer domain
    iat: int # time this token was issued
    exp: int # time after which this token has expired