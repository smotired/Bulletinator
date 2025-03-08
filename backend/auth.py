"""Authentication control module. Functionality for password hashing and JWT management."""

from datetime import datetime, UTC

import uuid
import bcrypt
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy import delete

from backend.config import settings
from backend.dependencies import Session
from backend.database import users as users_db
from backend.database.schema import DBUser, DBRefreshToken
from backend.exceptions import *
from backend.models.auth import AccessToken, AccessPayload, RefreshPayload, Login, LoginEmail, LoginUsername

def hash_password(password: str) -> str:
    """Hash a password with bcrypt.
    
    Args:
        password (str): The password to hash
        
    Returns:
        str: The password hashed using bcrypt and a random salt
    """
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def check_password(password: str, hashed_password: str) -> str:
    """Check a password with bcrypt.
    
    Args:
        password (str): The password to check
        hashed_password (str): The hashed password to check against
        
    Returns:
        bool: True if password hashes to hashed_password
    """
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
    
def generate_tokens(session: Session, form: Login) -> tuple[str, str]:
    """Generates access and refresh token JWTs from a login form.
    
    Args:
        session (Session): The database session
        form (Login): The username and password for an account

    Returns:
        str: An access token (JWT) for the account

    Raises:
        InvalidCredentials: if the username or password is invalid
    """
    # Verify login
    user: DBUser
    if isinstance(form, LoginUsername):
        user = users_db.get_by_username(form.username)
    elif isinstance(form, LoginEmail):
        user = users_db.get_by_email(form.email)
    else:
        raise InvalidCredentials()
    user = verify_user(user, form.password)
    # Generate an access token
    access_token = jwt.encode(
        _generate_access_payload(user).model_dump(),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    # Create a refresh token
    refresh_token = jwt.encode(
        _generate_refresh_payload(user).model_dump(),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    # Return these tokens
    return access_token, refresh_token

def verify_user(user: DBUser | None, password: str) -> DBUser:
    """Verify a user against a password.

    Args:
        user (DBUser | None): The account to verify
        password (str): The password supplied

    Returns:
        DBUser: The user that has been verified

    Raises:
        InvalidCredentials: If the password is incorrect for the user
    """
    # Can't verify if not logged in
    if user is None:
        raise InvalidCredentials()
    # Check password
    if not check_password(password, user.hashed_password):
        raise InvalidCredentials()
    return user

def extract_user(session: Session, token: str) -> DBUser:
    """Extract a user from an access token JWT
    
    Args:
        session (Session): The database session
        token (str): The access token JWT

    Returns:
        DBUser: The user tied to the token

    Raises:
        InvalidAccessToken: if the token is expired or invalid
    """
    # Get the information
    payload = _extract_access_payload(token)
    # Make sure the user exists
    user_id = int(payload['sub'])
    user = session.get(DBUser, user_id)
    if user is None:
        raise InvalidAccessToken()
    # Return the user
    return user

def refresh_access_token(session: Session, refresh_token: str) -> str:
    """Attempts to refresh an access token
    
    Args:
        session (Session): The database session
        refresh_token (str): The refresh token JWT
        
    Returns:
        str: The new access token
        
    Raises:
        InvalidRefreshToken: if the token is expired or invalid
    """
    # Verify the refresh token and extract the payload
    payload: RefreshPayload = _extract_refresh_payload(session, refresh_token)
    # Get the user
    user = session.get(DBUser, int(payload.sub))
    if user is None:
        raise InvalidRefreshToken()
    # Generate a new access token
    return jwt.encode(
        _generate_access_payload(user).model_dump(),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
def revoke_refresh_tokens(session: Session, user: DBUser):
    """Removes all refresh tokens for a user in the database, logging them out on all devices.
    
    Args:
        session (Session): The database session
        user (DBUser): The user to revoke access for
    """
    stmt = delete(DBRefreshToken).where(DBRefreshToken.user_id == user.id)
    session.exec(stmt)
    session.commit()

def _generate_access_payload(user: DBUser) -> AccessPayload:
    """Create a payload for an access token for this user.
    
    Args:
        user (DBUser): The user to create a token for
        
    Returns:
        AccessPayload: The JWT payload for this user
    """
    # Generate times
    iat = int(datetime.now(UTC).timestamp())
    exp = iat + settings.jwt_access_duration
    # Create the token
    return AccessPayload(
        sub=str(user.id),
        iss=settings.jwt_issuer,
        iat=iat,
        exp=exp
    )

def _extract_access_payload(token: str) -> AccessPayload:
    """Verify and extract payload from JWT access token.
    
    Args:
        token (str): The token
        
    Returns:
        AccessPayload: The payload of this JWT
        
    Raises:
        InvalidAccessToken: if the token has expired or was tampered with
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return AccessPayload(payload)
    except ExpiredSignatureError:
        raise InvalidAccessToken()
    except JWTError:
        raise InvalidAccessToken()

def _generate_refresh_payload(session: Session, user: DBUser) -> RefreshPayload:
    """Create a payload for an access token for this user.
    
    Args:
        session (Session): The database session
        user (DBUser): The user to create a token for
        
    Returns:
        RefreshPayload: The JWT payload for this user
    """
    # Generate times
    iat = int(datetime.now(UTC).timestamp())
    exp = iat + settings.jwt_refresh_duration
    # Create an ID for this token
    uid = uuid.uuid4()
    # Track in the database
    token = DBRefreshToken(token_id=uid, user_id=user.id, expires_at=exp)
    session.add(token)
    session.commit()
    # Create the token
    return RefreshPayload(
        sub=str(user.id),
        uid=uid,
        iss=settings.jwt_issuer,
        iat=iat,
        exp=exp
    )

def _extract_refresh_payload(session: Session, token: str) -> RefreshPayload:
    """Verify and extract payload from JWT refresh token.
    
    Args:
        token (str): The refresh token
        
    Returns:
        RefreshPayload: The payload of this JWT
        
    Raises:
        InvalidRefreshToken: if the token has expired or was tampered with
    """
    # extract the payload
    payload: dict
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
    except ExpiredSignatureError:
        raise InvalidRefreshToken()
    except JWTError:
        raise InvalidRefreshToken()
    # ensure it's actually in the database
    db_token: DBRefreshToken = session.get(DBRefreshToken, payload['uid'])
    if db_token is None or str(db_token.user_id) != payload['sub']:
        raise InvalidRefreshToken()
    # ensure it hasn't expired in the database and delete if it has
    if db_token.expires_at < int(datetime.now(UTC).timestamp()):
        session.delete(db_token)
        session.commit()
        raise InvalidRefreshToken()
    # return
    return RefreshPayload(payload)