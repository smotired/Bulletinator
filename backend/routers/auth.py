"""Router for authentication routes.

Args:
    router (APIRouter): Router for /auth routes
"""

from fastapi import APIRouter, Response, Form

from backend import auth
from backend.config import settings
from backend.database.schema import *
from backend.dependencies import DBSession, CurrentReadOnlyAccount, RefreshToken, set_cookie_secure
from backend.models.auth import AccessToken, Registration, Login
from backend.models.accounts import Account, AuthenticatedAccount

from typing import Annotated
from uuid import UUID

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/registration", status_code=201, response_model=AuthenticatedAccount)
def register_account(
    session: DBSession, # type: ignore
    form: Annotated[Registration, Form()]
) -> DBAccount:
    """Register new account"""
    return auth.register_account(session, form)

@router.post("/web/login", status_code=204)
def login_account(
    response: Response,
    session: DBSession, # type: ignore
    form: Annotated[Login, Form()]
) -> None:
    """Given an account login, generate access and refresh tokens.
    
    Access tokens are returned in the body and refresh tokens are added as a cookie."""
    access_token, refresh_token = auth.generate_tokens(session, form)
    set_cookie_secure(response, settings.jwt_access_cookie_key, access_token)
    set_cookie_secure(response, settings.jwt_refresh_cookie_key, refresh_token)
    return AccessToken(access_token=access_token, token_type="bearer")

@router.post("/web/refresh", status_code=204)
def refresh_access_token(
    response: Response,
    session: DBSession, # type: ignore
    refresh_token: RefreshToken
) -> None:
    """Generate a new access token using the refresh token."""
    access_token = auth.refresh_access_token(session, refresh_token)
    set_cookie_secure(response, settings.jwt_access_cookie_key, access_token)

@router.post("/web/logout", status_code=204)
def logout_account(
    response: Response,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount,
    token: RefreshToken
) -> None:
    """Authenticated route. Log out an account and invalidate the supplied refresh token."""
    auth.revoke_one_refresh_token(session, token)
    response.delete_cookie(settings.jwt_access_cookie_key)
    response.delete_cookie(settings.jwt_refresh_cookie_key)

@router.post("/token", status_code=200)
def login_account(
    session: DBSession, # type: ignore
    form: Annotated[Login, Form()]
) -> AccessToken:
    """Given an account login, generate access and refresh tokens.
    
    Access tokens are returned in the body and refresh tokens are added as a cookie."""
    access_token, _ = auth.generate_tokens(session, form)
    return AccessToken(access_token=access_token, token_type="bearer")
    
@router.post("/forcelogout", status_code=204)
def force_logout_account(
    response: Response,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount,
) -> None:
    """Authenticated route. Log out an account and invalidate ALL refresh tokens."""
    auth.revoke_refresh_tokens(session, account)
    response.delete_cookie(settings.jwt_access_cookie_key)
    response.delete_cookie(settings.jwt_refresh_cookie_key)

@router.post('/verify-email/{verification_id}', status_code=200, response_model=AuthenticatedAccount)
def verify_email(
    session: DBSession, # type: ignore
    verification_id: UUID,
) -> DBAccount:
    """Verify an account's email address"""
    return auth.verify_email(session, str(verification_id))