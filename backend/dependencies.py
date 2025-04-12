"""Dependencies for application.

Args:
    engine (sqlalchemy.engine.Engine): The database engine
    cookie_scheme (APIKeyCookie): The scheme to extract JWT from cookies
    bearer_scheme (HTTPBearer): The scheme to extract JWT from authorization headers
    DBSession (Session): A database session as a dependency
    CurrentAccount (DBAccount): The current account as a dependency
    RefreshToken (str): The refresh token as a dependency
"""

from typing import Annotated
import re

from fastapi import Depends
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database.schema import * # includes Base
from backend.exceptions import *

engine = create_engine(settings.db_url, echo=True)
Session = sessionmaker(bind=engine)

cookie_scheme = APIKeyCookie(name=settings.jwt_cookie_key, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

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
        
def get_access_token(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Access token extraction dependency. Depends on the bearer scheme.
    
    Extracts the access token JWT from the authorization headers."""
    if bearer is not None:
        return bearer.credentials
    raise NotAuthenticated()
        
def get_refresh_token(
    cookie_token: str | None = Depends(cookie_scheme),
) -> str:
    """Refresh token extraction dependency. Depends on the cookie scheme.
    
    Extracts the access token JWT from the cookies."""
    if cookie_token is not None:
        return cookie_token
    raise NotAuthenticated()

RefreshToken = Annotated[str, Depends(get_refresh_token)]

# gotta import this down here
from backend.auth import extract_account

def get_current_account(
    session: Session = Depends(get_session), # type: ignore
    access_token: str = Depends(get_access_token),
) -> DBAccount:
    """Current account dependency. Depends on the session and the access token."""
    return extract_account(session, access_token)

CurrentAccount = Annotated[DBAccount, Depends(get_current_account)]

# for times when authentication is not necessary but can change the results of a query

def get_optional_access_token(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    """Extracts the access token JWT from the authorization headers, if provided, or returns none"""
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