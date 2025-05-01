from sqlalchemy import select
import re
from json import dumps

from backend.dependencies import DBSession
from backend.database.schema import DBAccount, DBCustomer, DBEmailVerification, DBAuthEvent
from backend.exceptions import *

from backend import auth
from backend.utils import email_handler
from backend.utils import stripe
from backend.models.accounts import AccountUpdate, AuthenticatedAccount

# Account creation logic will be handled only by authentication module

def get_by_id(session: DBSession, account_id: str) -> DBAccount: # type: ignore
    """Retrieve account by email"""
    account = session.get(DBAccount, account_id)
    if account is None:
        raise EntityNotFound("account", "id", account_id)
    return account

def get_by_stripe_id(session: DBSession, stripe_id: str) -> DBCustomer: # type: ignore
    """Retrieve customer object by stripe ID"""
    customer: DBCustomer = session.get(DBCustomer, stripe_id)
    if customer is None:
        raise EntityNotFound("customer", "stripe_id", stripe_id)
    return customer

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

def get_all(session: DBSession) -> list[DBAccount]: # type: ignore
    """Retrieve all accounts"""
    return list(session.execute(select(DBAccount)).scalars().all())

def force_get_by_username(session: DBSession, username: str) -> DBAccount: # type: ignore
    """Raise 404 if no account has this username"""
    account: DBAccount | None = get_by_username(session, username)
    if account is None:
        raise EntityNotFound('account', 'username', username)
    return account

def update(host: str, session: DBSession, account: DBAccount, update: AccountUpdate) -> DBAccount: # type: ignore
    """Updates an account with non-sensitive information"""
    # Make sure the username isn't taken, and update it
    if update.username is not None and update.username != account.username:
        if get_by_username(session, update.username) is not None:
            raise DuplicateEntity("account", "username", update.username)
        if len(update.username) > 64:
            raise FieldTooLong('username')
        if not re.fullmatch(r'[A-Za-z0-9_]+', update.username):
            raise InvalidField(update.username, 'username')
        account.username = update.username
    # Update the filename for the image (so they can just link to images hosted elsewhere)
    if update.profile_image is not None:
        account.profile_image = update.profile_image
    if update.display_name is not None:
        account.display_name = update.display_name if len(update.display_name) > 0 else None
    
    # Check if the password is correct
    verified = (auth.verify_account(account, update.old_password) is not None) if update.old_password is not None else False
    
    # Make sure the email isn't taken, and update it
    updating_email = False
    if update.email is not None and update.email != account.email:
        if not verified:
            raise InvalidCredentials()
        if get_by_email(session, update.email) is not None:
            raise DuplicateEntity("account", "email", update.email)
        if len(update.email) > 64:
            raise FieldTooLong('email')
        if update.email.count('@') != 1: # this is all we will do for validation
            raise InvalidField(update.email, 'email')
        updating_email = True
    # Update the password
    if update.new_password is not None:
        if not verified:
            raise InvalidCredentials()
        account.hashed_password = auth.hash_password(update.new_password)
        
    # Update in DB
    session.add(account)
    session.commit()
    session.refresh(account)
    event = DBAuthEvent(account_id=account.id, event_type="account_update" if not verified else "sensitive_update", host=host, detail=dumps({
        "account": AuthenticatedAccount.model_validate(account.__dict__).model_dump(),
        "config": update.model_dump()
    }))
    session.add(event)
    session.commit()
    # Create a verification email
    if updating_email: # already did validation
        verification = DBEmailVerification( account_id=account.id, email=update.email)
        account.email_verification = verification
        session.add(account)
        session.commit()
        session.refresh(account)
        email_handler.send_update_verification_email(account, verification)
    return account

def delete(host: str, session: DBSession, account: DBAccount) -> None: # type: ignore
    """Delete an account and log an event"""
    stripe.delete_customer(account.customer)
    session.delete(account)
    event = DBAuthEvent(account_id=account.id, event_type="deletion", host=host, detail=dumps(AuthenticatedAccount.model_validate(account.__dict__).model_dump()))
    session.add(event)
    session.commit()