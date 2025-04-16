"""Dependencies for application.

Args:
    engine (sqlalchemy.engine.Engine): The database engine
    access_cookie_scheme (APIKeyCookie): The scheme to extract access token JWT from cookies
    refresh_cookie_scheme (APIKeyCookie): The scheme to extract refresh token JWT from cookies
    bearer_scheme (HTTPBearer): The scheme to extract access token JWT from authorization headers
    DBSession (Session): A database session as a dependency
    CurrentAccount (DBAccount): The current account as a dependency
    RefreshToken (str): The refresh token as a dependency
"""

from typing import Annotated
import re
from datetime import datetime, UTC

from fastapi import Depends, Response
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import create_engine, text, delete
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database.schema import * # includes Base
from backend.exceptions import *

engine = create_engine(settings.db_url, echo=True)
Session = sessionmaker(bind=engine)

access_cookie_scheme = APIKeyCookie(name=settings.jwt_access_cookie_key, auto_error=False)
refresh_cookie_scheme = APIKeyCookie(name=settings.jwt_refresh_cookie_key, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# Database functions

def create_db_tables():
    """Ensure the database and tables are created."""

    Base.metadata.create_all(engine)

    if settings.db_sqlite:
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_key=ON"))

def get_session():
    """Database session dependency."""

    with Session() as session:
        yield session

DBSession = Annotated[Session, Depends(get_session)]

def cleanup_db():
    """Cleans up unused entries from certain tables in the database"""
    with Session() as session:
        # Remove expired refresh tokens
        statement = delete(DBRefreshToken).where(DBRefreshToken.expires_at < datetime.now(UTC).timestamp())
        session.execute(statement)
        session.commit()
        # Remove expired email verifications
        statement = delete(DBEmailVerification).where(DBEmailVerification.expires_at < datetime.now(UTC).replace(tzinfo=None))
        session.execute(statement)
        session.commit()
        # Remove accounts that have no email and no pending email verifications
        statement = delete(DBAccount).where((DBAccount.email == None) & (DBAccount.email_verification == None))
        session.execute(statement)
        session.commit()
        # Remove expired editor invitations
        statement = delete(DBEditorInvitation).where(DBEditorInvitation.expires_at < datetime.now(UTC).replace(tzinfo=None))
        session.execute(statement)
        session.commit()

# Authentication Functions
        
def get_access_token(
    cookie_token: str | None = Depends(access_cookie_scheme),
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Access token extraction dependency. Depends on the bearer scheme.
    
    Extracts the access token JWT from the authorization headers."""
    if cookie_token is not None:
        return cookie_token
    if bearer is not None:
        return bearer.credentials
    raise NotAuthenticated()
        
def get_refresh_token(
    cookie_token: str | None = Depends(refresh_cookie_scheme),
) -> str:
    """Refresh token extraction dependency. Depends on the cookie scheme.
    
    Extracts the access token JWT from the cookies."""
    if cookie_token is not None:
        return cookie_token
    raise NotAuthenticated()

RefreshToken = Annotated[str, Depends(get_refresh_token)]

# account dependencies

# gotta import this down here
from backend.auth import extract_account

# an account with only read permissions

def get_current_account(
    session: Session = Depends(get_session), # type: ignore
    access_token: str = Depends(get_access_token),
) -> DBAccount:
    """Current account dependency. Depends on the session and the access token."""
    return extract_account(session, access_token)

CurrentReadOnlyAccount = Annotated[DBAccount, Depends(get_current_account)]

# non read-only account requires a verified email

def get_current_verified_account(
    account: DBAccount = Depends(get_current_account),
) -> DBAccount:
    """Current account dependency. Depends on the session and the access token."""
    if account.email is None:
        raise UnverifiedEmailAddress()
    return account

CurrentAccount = Annotated[DBAccount, Depends(get_current_verified_account)]

# for times when authentication is not necessary but can change the results of a query

def get_optional_access_token(
    cookie_token: str | None = Depends(access_cookie_scheme),
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    """Extracts the access token JWT from the authorization headers, if provided, or returns none"""
    if cookie_token is not None:
        return cookie_token
    if bearer is not None:
        return bearer.credentials
    return None

def get_optional_account(
    session: Session = Depends(get_session), # type: ignore
    access_token: str = Depends(get_optional_access_token),
) -> Optional[DBAccount]:
    """Optional account dependency. Depends on the session and the access token. Returns the current account if one is logged in, or None if login fails.
    
    Used for routes that don't *require* a login, but can change the results if someone *is* logged in."""
    if access_token is None:
        return None
    return extract_account(session, access_token)

OptionalAccount = Annotated[Optional[DBAccount], Depends(get_optional_account)]

def format_list(items: list[str]):
    """Formats a list nicely in alphabetical order. 'Alice, Bob, Charlie'"""
    items = sorted(items)
    if len(items) == 0:
        return ""
    return ', '.join(items)

def name_to_identifier(name: str):
    """Converts a name to an alphanumeric identifier"""
    # convert "whitespace" to underscores
    identifier = re.sub(r"[ -]+", "_", name)
    # remove disallowed characters
    identifier = re.sub(r"[^A-ZA-Za-z0-9_]", "", identifier)
    # collapse underscores
    identifier = re.sub(r"__+", "_", identifier)
    return identifier

def set_cookie_secure(response: Response, key: str, value: str):
    response.set_cookie(
        key=key,
        value=value,
        max_age=settings.cookie_max_age,
        httponly=True,
        secure=False, # change to True once we serve over HTTPS
        samesite='lax'
    )