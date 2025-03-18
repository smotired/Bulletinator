"""Router for user routes.

Args:
    router (APIRouter): Router for /users routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend import auth
from backend.database import users as users_db
from backend.dependencies import DBSession, CurrentUser
from backend.models.users import User, UserCollection, UserUpdateForm
from backend.models.shared import Metadata
from backend.config import settings

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/", status_code=200)
def get_users(
    session: DBSession
) -> UserCollection:
    """Get a list of all accounts"""
    dbusers_list = users_db.get_all(session)
    return UserCollection(
        metadata=Metadata(count=len(dbusers_list)),
        users=[ User(**dbuser.model_dump) for dbuser in dbusers_list ]
    )

@router.get("/me", status_code=200, response_model=User)
def get_current_user(
    session: DBSession,
    user: CurrentUser
) -> DBUser:
    """Get the currently authenticated account"""
    return users_db.get_by_id(session, user.id)

@router.put("/me", status_code=200, response_model=User)
def update_current_user(
    session: DBSession,
    user: CurrentUser,
    update: UserUpdateForm
) -> DBUser:
    """Update the currently authenticated account"""
    return users_db.update(session, user, update)

@router.delete("/me", status_code=204)
def delete_current_user(
    response: Response,
    session: DBSession,
    user: CurrentUser
) -> None:
    """Delete the currently authenticated account and log out"""
    users_db.delete(session.user)
    auth.revoke_refresh_tokens(session, user)
    response.delete_cookie(settings.jwt_cookie_key)