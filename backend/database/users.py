from sqlalchemy import select

from backend.dependencies import DBSession
from backend.database.schema import DBUser
from backend.exceptions import *

from backend import auth
from backend.models.users import UserUpdate

# User creation logic will be handled only by authentication module

def get_by_id(session: DBSession, user_id: int) -> DBUser:
    """Retrieve account by email"""
    user = session.get(DBUser, user_id)
    if user is None:
        raise EntityNotFound("user", "id", user_id)
    return user

def get_by_email(session: DBSession, email: str) -> DBUser | None:
    """Retrieve account by email"""
    stmt = select(DBUser).where(DBUser.email == email)
    return session.execute(stmt).scalars().one_or_none()

def get_by_username(session: DBSession, username: str) -> DBUser | None:
    """Retrieve account by email"""
    stmt = select(DBUser).where(DBUser.username == username)
    return session.execute(stmt).scalars().one_or_none()

def get_all(session: DBSession) -> list[DBUser]:
    """Retrieve all accounts"""
    return list(session.execute(select(DBUser)).scalars().all())

def update(session: DBSession, user: DBUser, update: UserUpdate) -> DBUser:
    """Updates a user with non-sensitive information"""
    # Make sure the username isn't taken, and update it
    if update.username is not None and update.username != user.username:
        if get_by_username(session, update.username) is not None:
            raise DuplicateEntity("user", "username", update.username)
        user.username = update.username
    # TODO: Once image uploading is implemented, make sure the image at this filename exists and is owned by the user
    
    # Check if the password is correct
    verified = (auth.verify_user(user, update.old_password) is not None) if update.old_password is not None else False
    
    # Make sure the email isn't taken, and update it
    if update.email is not None and update.email != user.email:
        if not verified:
            raise InvalidCredentials()
        if get_by_email(session, update.email) is not None:
            raise DuplicateEntity("user", "email", update.email)
        user.email = update.email
    # Update the password
    if update.new_password is not None:
        if not verified:
            raise InvalidCredentials()
        user.hashed_password = auth.hash_password(update.new_password)
        
    # Update in DB
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete(session: DBSession, account: DBUser) -> None:
    """Delete an account."""
    session.delete(account)
    session.commit()