from sqlalchemy import select

from backend.dependencies import Session
from backend.database.schema import DBUser
from backend.exceptions import *

from backend import auth
from backend.models.auth import Registration
from backend.models.users import UserUpdate, PasswordUpdate

def create(session: Session, form: Registration) -> DBUser:
    """Creates a user with this login information."""
    # Make sure the username and email are not already registered
    if get_by_email(form.email) is not None:
        raise DuplicateEntity("user", "email", form.email)
    if get_by_email(form.username) is not None:
        raise DuplicateEntity("user", "username", form.username)
    # Hash the password
    hashed = auth.hash_password(form.password)
    # Create the user
    new_user = DBUser(
        username=form.username,
        email=form.email,
        hashed_password=hashed
    )
    # Add and return
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

def get_by_id(session: Session, user_id: int) -> DBUser:
    """Retrieve account by email"""
    user = session.get(DBUser, user_id)
    if user is None:
        raise EntityNotFound("user", "id", user_id)
    return user

def get_by_email(session: Session, email: str) -> DBUser | None:
    """Retrieve account by email"""
    stmt = select(DBUser).where(DBUser.email == email)
    return session.exec(stmt).one_or_none()

def get_by_username(session: Session, username: str) -> DBUser | None:
    """Retrieve account by email"""
    stmt = select(DBUser).where(DBUser.username == username)
    return session.exec(stmt).one_or_none()

def get_all(session: Session) -> list[DBUser]:
    """Retrieve all accounts"""
    return list(session.exec(select(DBUser)).all())

def update(session: Session, user: DBUser, update: UserUpdate) -> DBUser:
    """Updates a user with non-sensitive information"""
    # Make sure the username isn't taken, and update it
    if update.username is not None and update.username != user.username:
        if get_by_username(session, update.username) is not None:
            raise DuplicateEntity("user", "username", update.username)
        user.username = update.username
    # TODO: Make sure the image exists and update that, once image uploading is developed
    # Update in DB
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def update_sensitive(session: Session, user: DBUser, update: PasswordUpdate) -> DBUser:
    """Updates a user's sensitive information"""
    # Make sure the password is correct
    user = auth.verify_user(user, update.old_password)
    # Make sure the email isn't taken, and update it
    if update.email is not None and update.email != user.email:
        if get_by_email(session, update.email) is not None:
            raise DuplicateEntity("user", "email", update.email)
        user.email = update.email
    # Update the password
    if update.new_password is not None:
        user.hashed_password = auth.hash_password(update.new_password)
    # Update in DB
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete(session: Session, account: DBUser) -> None:
    """Delete an account."""
    session.delete(account)
    session.commit()