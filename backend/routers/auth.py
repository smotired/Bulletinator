"""Router for authentication routes.

Args:
    router (APIRouter): Router for /auth routes
"""

from fastapi import APIRouter, Response

from backend import auth
from backend.config import settings
from backend.database.schema import *
from backend.database import users as users_db
from backend.dependencies import DBSession, CurrentUser, RefreshToken
from backend.models.auth import RegistrationForm, LoginForm, AccessToken
from backend.models.users import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/registration", status_code=201, response_model=User)
def register_account(
    session: DBSession,
    form: RegistrationForm
) -> DBUser:
    """Register new account"""
    return users_db.create(session, form)

@router.post("/login", status_code=200)
def login_user(
    response: Response,
    session: DBSession,
    form: LoginForm
) -> AccessToken:
    """Given an account login, generate access and refresh tokens.
    
    Access tokens are returned in the body and refresh tokens are added as a cookie."""
    access_token, refresh_token = auth.generate_tokens(session, form)
    response.set_cookie(settings.jwt_cookie_key, refresh_token, httponly=True)
    return AccessToken(access_token=access_token, token_type="bearer")

@router.post("/refresh", status_code=200)
def refresh_access_token(
    session: DBSession,
    refresh_token: RefreshToken
) -> AccessToken:
    """Generate a new access token using the refresh token."""
    access_token = auth.refresh_access_token(session, refresh_token)
    return AccessToken(access_token=access_token, token_type="bearer")

@router.post("/logout", status_code=204)
def logout_user(
    response: Response,
    session: DBSession,
    user: CurrentUser,
    token: RefreshToken
) -> None:
    """Authenticated route. Log out a user and invalidate the supplied refresh token."""
    auth.revoke_one_refresh_token(session, token)
    response.delete_cookie(settings.jwt_cookie_key)
    
@router.post("/forcelogout", status_code=204)
def force_logout_user(
    response: Response,
    session: DBSession,
    user: CurrentUser,
) -> None:
    """Authenticated route. Log out a user and invalidate ALL refresh tokens."""
    auth.revoke_refresh_tokens(session, user)
    response.delete_cookie(settings.jwt_cookie_key)