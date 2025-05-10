"""Router for account routes.

Args:
    router (APIRouter): Router for /accounts routes
"""

from fastapi import APIRouter, Response, Request
from uuid import UUID

from backend.database.schema import *
from backend import auth
from backend.utils.rate_limiter import limit
from backend.database import accounts as accounts_db, media as media_db
from backend.dependencies import DBSession, CurrentAccount, CurrentReadOnlyAccount
from backend.models.accounts import Account, AuthenticatedAccount, AccountUpdate
from backend.models.media import Image
from backend.models.shared import CollectionFactory
from backend.config import settings

router = APIRouter(prefix="/accounts", tags=["Account"])

@router.get("/", status_code=200, response_model=CollectionFactory(Account, DBAccount))
@limit("main")
def get_accounts(
    request: Request,
    session: DBSession # type: ignore
) -> list[DBAccount]:
    """Get a list of all accounts"""
    return accounts_db.get_all(session)

@router.get("/me", status_code=200, response_model=AuthenticatedAccount)
@limit("account")
def get_current_account(
    request: Request,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount
) -> DBAccount:
    """Get the currently authenticated account"""
    return accounts_db.get_by_id(session, account.id)

@router.put("/me", status_code=200, response_model=AuthenticatedAccount)
@limit("account")
def update_current_account(
    request: Request,
    session: DBSession, # type: ignore
    account: CurrentAccount,
    update: AccountUpdate
) -> DBAccount:
    """Update the currently authenticated account"""
    return accounts_db.update(request.client.host, session, account, update)

@router.delete("/me", status_code=204)
@limit("account", no_content=True)
def delete_current_account(
    request: Request,
    response: Response,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount
) -> None:
    """Delete the currently authenticated account and log out"""
    accounts_db.delete(request.client.host, session, account)
    auth.revoke_refresh_tokens(request.client.host, session, account)
    response.delete_cookie(settings.jwt_refresh_cookie_key)

@router.get("/me/uploads/images", status_code=200, response_model=CollectionFactory(Image, DBImage))
@limit("account")
def get_current_account(
    request: Request,
    session: DBSession, # type: ignore
    account: CurrentReadOnlyAccount
) -> list[DBImage]:
    """Get a list of images uploaded by the current account"""
    return media_db.get_account_images(session, account)

@router.get("/{account_id:uuid}", status_code=200, response_model=Account)
@limit("account")
def get_account_by_id(
    request: Request,
    session: DBSession, # type: ignore
    account_id: UUID
) -> DBAccount:
    """Gets an account object"""
    return accounts_db.get_by_id(session, str(account_id))

@router.get("/{username}", status_code=200, response_model=Account)
@limit("account")
def get_account_by_username(
    request: Request,
    session: DBSession, # type: ignore
    username: str
) -> DBAccount:
    """Gets an account object by the username"""
    return accounts_db.force_get_by_username(session, username)