"""Router for authentication routes.

Args:
    router (APIRouter): Router for /auth routes
"""

from fastapi import APIRouter, Request, Response, Form

from backend import auth
from backend.utils.rate_limiter import limit
from backend.config import settings
from backend.database.schema import *
from backend.dependencies import DBSession, CurrentReadOnlyAccount, RefreshToken, OptionalRefreshToken, set_cookie_secure
from backend.models.auth import AccessToken, Registration, Login, PasswordChange
from backend.models.accounts import AuthenticatedAccount

from typing import Annotated
from uuid import UUID

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/registration", status_code=201, response_model=AuthenticatedAccount)
@limit("auth")
def register_account(
    request: Request,
    session: DBSession, # type: ignore
    form: Annotated[Registration, Form()]
) -> DBAccount:
    """Register new account"""
    return auth.register_account(request.client.host, session, form)

@router.post("/web/login", status_code=204)
@limit("auth", no_content=True)
def get_token(
    request: Request,
    response: Response,
    session: DBSession, # type: ignore
    form: Annotated[Login, Form()]
) -> None:
    """Given an account login, generate access and refresh tokens.
    
    Access tokens are returned in the body and refresh tokens are added as a cookie."""
    access_token, refresh_token = auth.generate_tokens(session, form, request.client.host)
    set_cookie_secure(response, settings.jwt_access_cookie_key, access_token)
    set_cookie_secure(response, settings.jwt_refresh_cookie_key, refresh_token)
    return AccessToken(access_token=access_token, token_type="bearer")

@router.post("/web/refresh", status_code=204)
@limit("auth", no_content=True)
def refresh_access_token(
    request: Request,
    response: Response,
    session: DBSession, # type: ignore
    refresh_token: RefreshToken
) -> None:
    """Generate a new access token using the refresh token."""
    access_token = auth.refresh_access_token(session, refresh_token)
    set_cookie_secure(response, settings.jwt_access_cookie_key, access_token)

@router.post("/web/logout", status_code=204)
@limit("auth", no_content=True)
def logout_account(
    request: Request,
    response: Response,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount,
    token: OptionalRefreshToken
) -> None:
    """Authenticated route. Log out an account and invalidate the supplied refresh token."""
    if token is not None:
        auth.revoke_one_refresh_token(request.client.host, session, token)
    response.delete_cookie(settings.jwt_access_cookie_key)
    response.delete_cookie(settings.jwt_refresh_cookie_key)

@router.post("/token", status_code=200)
@limit("auth")
def get_token(
    request: Request,
    session: DBSession, # type: ignore
    form: Annotated[Login, Form()]
) -> AccessToken:
    """Given an account login, generate access and refresh tokens.
    
    Access tokens are returned in the body and refresh tokens are added as a cookie."""
    access_token, _ = auth.generate_tokens(session, form)
    return AccessToken(access_token=access_token, token_type="bearer")
    
@router.post("/forcelogout", status_code=204)
@limit("auth", no_content=True)
def force_logout_account(
    request: Request,
    response: Response,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount,
) -> None:
    """Authenticated route. Log out an account and invalidate ALL refresh tokens."""
    auth.revoke_refresh_tokens(request.client.host, session, account)
    response.delete_cookie(settings.jwt_access_cookie_key)
    response.delete_cookie(settings.jwt_refresh_cookie_key)

@router.post('/verify-email/{verification_id}', status_code=200, response_model=AuthenticatedAccount)
@limit("from_email")
def verify_email(
    request: Request,
    session: DBSession, # type: ignore
    verification_id: UUID,
) -> DBAccount:
    """Verify an account's email address"""
    return auth.verify_email(request.client.host, session, str(verification_id))

@router.post('/request-change-password', status_code=204, response_model=None)
@limit("from_email")
def request_change_password(
    request: Request,
    session: DBSession, # type: ignore
    email: str
) -> None:
    """Change account password"""
    auth.request_password_change(request.client.host, session, email)

@router.post('/change-password/{request_id}', status_code=200, response_model=AuthenticatedAccount)
@limit("from_email")
def change_password(
    request: Request,
    session: DBSession, # type: ignore
    request_id: UUID,
    form: Annotated[PasswordChange, Form()],
) -> DBAccount:
    """Change account password"""
    return auth.password_change(request.client.host, session, str(request_id), form)