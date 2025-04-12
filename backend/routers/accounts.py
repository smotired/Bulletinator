"""Router for account routes.

Args:
    router (APIRouter): Router for /accounts routes
"""

from fastapi import APIRouter, Response
from uuid import UUID

from backend.database.schema import *
from backend import auth
from backend.database import accounts as accounts_db
from backend.database import media as media_db
from backend.dependencies import DBSession, CurrentAccount
from backend.models.accounts import Account, AuthenticatedAccount, AccountCollection, AccountUpdate, convert_account, convert_account_list, convert_auth_account
from backend.models.media import Image, ImageCollection
from backend.models.shared import Metadata
from backend.config import settings

router = APIRouter(prefix="/accounts", tags=["Account"])

@router.get("/", status_code=200)
def get_accounts(
    session: DBSession # type: ignore
) -> AccountCollection:
    """Get a list of all accounts"""
    accounts = accounts_db.get_all(session)
    return AccountCollection(
        metadata=Metadata(count=len(accounts)),
        accounts=convert_account_list( accounts )
    )

@router.get("/me", status_code=200, response_model=AuthenticatedAccount)
def get_current_account(
    session: DBSession, # type: ignore
    account: CurrentAccount
) -> DBAccount:
    """Get the currently authenticated account"""
    return accounts_db.get_by_id(session, account.id)

@router.put("/me", status_code=200, response_model=AuthenticatedAccount)
def update_current_account(
    session: DBSession, # type: ignore
    account: CurrentAccount,
    update: AccountUpdate
) -> DBAccount:
    """Update the currently authenticated account"""
    return accounts_db.update(session, account, update)

@router.delete("/me", status_code=204)
def delete_current_account(
    response: Response,
    session: DBSession, # type: ignore
    account: CurrentAccount
) -> None:
    """Delete the currently authenticated account and log out"""
    accounts_db.delete(session, account)
    auth.revoke_refresh_tokens(session, account)
    response.delete_cookie(settings.jwt_refresh_cookie_key)

@router.get("/me/uploads/images", status_code=200, response_model=ImageCollection)
def get_current_account(
    session: DBSession, # type: ignore
    account: CurrentAccount
) -> ImageCollection:
    """Get a list of images uploaded by the current account"""
    images = media_db.get_account_images(session, account)
    return ImageCollection(
        metadata=Metadata(count=len(images)),
        images=[ Image.model_validate(image.__dict__) for image in images ]
    )

@router.get("/{account_id:uuid}", status_code=200, response_model=Account)
def get_account(
    session: DBSession, # type: ignore
    account_id: UUID
) -> DBAccount:
    """Gets an account object"""
    return accounts_db.get_by_id(session, str(account_id))

@router.get("/{username}", status_code=200, response_model=Account)
def get_account(
    session: DBSession, # type: ignore
    username: str
) -> DBAccount:
    """Gets an account object by the username"""
    return accounts_db.force_get_by_username(session, username)