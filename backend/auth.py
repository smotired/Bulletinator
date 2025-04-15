"""Authentication control module. Functionality for password hashing and JWT management."""

from datetime import datetime, UTC

import uuid
import bcrypt
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy import select, delete
import re

from backend.config import settings
from backend.dependencies import DBSession
from backend.database.schema import DBAccount, DBRefreshToken, DBPermission, DBEmailVerification
from backend.exceptions import *
from backend.models.auth import AccessPayload, RefreshPayload, Login, Registration
from backend import email_handler

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

# gotta repeat these here because of circular imports
def get_by_email(session: DBSession, email: str) -> DBAccount | None: # type: ignore
    """Retrieve account by email"""
    stmt = select(DBAccount).where(DBAccount.email == email)
    account: DBAccount | None = session.execute(stmt).scalars().one_or_none()
    if account is not None:
        return account
    stmt = select(DBEmailVerification).where(DBEmailVerification.email == email) # also check unverified emails
    verification: DBEmailVerification | None = session.execute(stmt).scalars().one_or_none()
    return verification.account if verification is not None else None

def get_by_username(session: DBSession, username: str) -> DBAccount | None: # type: ignore
    """Retrieve account by email"""
    stmt = select(DBAccount).where(DBAccount.username == username)
    return session.execute(stmt).scalars().one_or_none()

def register_account(session: DBSession, form: Registration) -> DBAccount: # type: ignore
    """Creates an account in the database for this account
    
    Args:
        session (Session): The database session
        form (Registration): The username, email, and password for a new account

    Returns:
        DBAccount: An Account object for the registered account

    Raises:
        DuplicateEntity: if the username or email is already taken
    """
    # Make sure the username and email are not already registered
    if get_by_email(session, form.email) is not None:
        raise DuplicateEntity("account", "email", form.email)
    if get_by_username(session, form.username) is not None:
        raise DuplicateEntity("account", "username", form.username)
    # Validation
    if len(form.email) > 64:
        raise FieldTooLong('email')
    if form.email.count('@') != 1:
        raise InvalidField(form.email, 'email')
    if len(form.username) > 64:
        raise FieldTooLong('username')
    if not re.fullmatch(r'[A-Za-z0-9_]+', form.username):
        raise InvalidField(form.username, 'username')
    # Create the account
    new_account = DBAccount(
        username=form.username,
        email=None,
        hashed_password=hash_password(form.password)
    )
    # Add and setup
    session.add(new_account)
    session.commit()
    session.refresh(new_account)
    new_account.permission = DBPermission( account_id=new_account.id )
    session.add(new_account)
    session.commit()
    # Send email verification
    email_verification = DBEmailVerification( account_id=new_account.id, email=form.email )
    session.add(email_verification)
    session.commit()
    session.refresh(email_verification)
    email_handler.send_verification_email(new_account, email_verification)
    # Return
    return new_account
    
def generate_tokens(session: DBSession, form: Login) -> tuple[str, str]: # type: ignore
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
    account: DBAccount = get_by_email(session, form.identifier)
    if account is None:
        account = get_by_username(session, form.identifier)
    if account is None:
        raise InvalidCredentials()
    account = verify_account(account, form.password)
    # Generate an access token
    access_token = jwt.encode(
        _generate_access_payload(account).model_dump(),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    # Create a refresh token
    refresh_token = jwt.encode(
        _generate_refresh_payload(session, account).model_dump(),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    # Return these tokens
    return access_token, refresh_token

def verify_account(account: DBAccount | None, password: str) -> DBAccount:
    """Verify an account against a password.

    Args:
        account (DBAccount | None): The account to verify
        password (str): The password supplied

    Returns:
        DBAccount: The account that has been verified

    Raises:
        InvalidCredentials: If the password is incorrect for the account
    """
    # Can't verify if not logged in
    if account is None:
        raise InvalidCredentials()
    # Check password
    if not check_password(password, account.hashed_password):
        raise InvalidCredentials()
    return account

def extract_account(session: DBSession, token: str) -> DBAccount: # type: ignore
    """Extract an account from an access token JWT
    
    Args:
        session (Session): The database session
        token (str): The access token JWT

    Returns:
        DBAccount: The account tied to the token

    Raises:
        InvalidAccessToken: if the token is expired or invalid
    """
    # Get the information
    payload = _extract_access_payload(token)
    # Make sure the account exists
    account_id = payload.sub
    account = session.get(DBAccount, account_id)
    if account is None:
        raise InvalidAccessToken()
    # Return the account
    return account

def refresh_access_token(session: DBSession, refresh_token: str) -> str: # type: ignore
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
    # Get the account
    account = session.get(DBAccount, payload.sub)
    if account is None:
        raise InvalidRefreshToken()
    # Generate a new access token
    return jwt.encode(
        _generate_access_payload(account).model_dump(),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
def revoke_one_refresh_token(session: DBSession, token: str): # type: ignore
    """Removes a refresh tokens for an account in the database, ensuring it cannot be used to log in again.
    
    Args:
        session (Session): The database session
        token (str): The refresh token to revoke
    """
    # Verify the refresh token and extract the payload
    payload: RefreshPayload = _extract_refresh_payload(session, token)
    stmt = delete(DBRefreshToken).where(DBRefreshToken.token_id == payload.uid)
    session.execute(stmt)
    session.commit()
    
def revoke_refresh_tokens(session: DBSession, account: DBAccount): # type: ignore
    """Removes all refresh tokens for an account in the database, logging them out on all devices.
    
    Args:
        session (Session): The database session
        account (DBAccount): The account to revoke access for
    """
    stmt = delete(DBRefreshToken).where(DBRefreshToken.account_id == account.id)
    session.execute(stmt)
    session.commit()

def _generate_access_payload(account: DBAccount) -> AccessPayload:
    """Create a payload for an access token for this account.
    
    Args:
        account (DBAccount): The account to create a token for
        
    Returns:
        AccessPayload: The JWT payload for this account
    """
    # Generate times
    iat = int(datetime.now(UTC).timestamp())
    exp = iat + settings.jwt_access_duration
    # Create the token
    return AccessPayload(
        sub=str(account.id),
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
        return AccessPayload(**payload)
    except ExpiredSignatureError:
        raise InvalidAccessToken()
    except JWTError:
        raise InvalidAccessToken()

def _generate_refresh_payload(session: DBSession, account: DBAccount) -> RefreshPayload: # type: ignore
    """Create a payload for an access token for this account.
    
    Args:
        session (Session): The database session
        account (DBAccount): The account to create a token for
        
    Returns:
        RefreshPayload: The JWT payload for this account
    """
    # Generate times
    iat = int(datetime.now(UTC).timestamp())
    exp = iat + settings.jwt_refresh_duration
    # Create an ID for this token
    uid = str(uuid.uuid4())
    # Track in the database
    token = DBRefreshToken(token_id=uid, account_id=account.id, expires_at=exp)
    session.add(token)
    session.commit()
    # Create the token
    return RefreshPayload(
        sub=str(account.id),
        uid=uid,
        iss=settings.jwt_issuer,
        iat=iat,
        exp=exp
    )

def _extract_refresh_payload(session: DBSession, token: str) -> RefreshPayload: # type: ignore
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
    if db_token is None or str(db_token.account_id) != payload['sub']:
        raise InvalidRefreshToken()
    # ensure it hasn't expired in the database and delete if it has
    if db_token.expires_at < int(datetime.now(UTC).timestamp()):
        session.delete(db_token)
        session.commit()
        raise InvalidRefreshToken()
    # return
    return RefreshPayload(**payload)

def verify_email(session: DBSession, verification_id: str) -> DBAccount: # type: ignore
    """Verify an email account and update it."""
    # Get and check the verification
    verification: DBEmailVerification | None = session.get(DBEmailVerification, verification_id)
    if verification is None or verification.expires_at.astimezone(UTC) < datetime.now(UTC):
        raise InvalidEmailVerification()
    # Update their email
    account: DBAccount = verification.account
    account.email = verification.email
    session.add(account)
    session.delete(verification)
    session.commit()
    session.refresh(account)
    return account