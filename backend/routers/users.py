"""Router for user routes.

Args:
    router (APIRouter): Router for /users routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend import auth
from backend.database import users as users_db
from backend.database import media as media_db
from backend.dependencies import DBSession, CurrentUser
from backend.models.users import User, AuthenticatedUser, UserCollection, UserUpdate, convert_user, convert_user_list, convert_auth_user
from backend.models.media import Image, ImageCollection
from backend.models.shared import Metadata
from backend.config import settings

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/", status_code=200)
def get_users(
    session: DBSession
) -> UserCollection:
    """Get a list of all accounts"""
    users = users_db.get_all(session)
    return UserCollection(
        metadata=Metadata(count=len(users)),
        users=convert_user_list( users )
    )

@router.get("/me", status_code=200, response_model=AuthenticatedUser)
def get_current_user(
    session: DBSession,
    user: CurrentUser
) -> DBUser:
    """Get the currently authenticated account"""
    return users_db.get_by_id(session, user.id)

@router.put("/me", status_code=200, response_model=AuthenticatedUser)
def update_current_user(
    session: DBSession,
    user: CurrentUser,
    update: UserUpdate
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
    users_db.delete(session, user)
    auth.revoke_refresh_tokens(session, user)
    response.delete_cookie(settings.jwt_cookie_key)

@router.get("/me/uploads/images", status_code=200, response_model=ImageCollection)
def get_current_user(
    session: DBSession,
    user: CurrentUser
) -> ImageCollection:
    """Get a list of images uploaded by the current account"""
    images = media_db.get_user_images(session, user)
    return ImageCollection(
        metadata=Metadata(count=len(images)),
        images=[ Image.model_validate(image.__dict__) for image in images ]
    )

@router.get("/{user_id}", status_code=200, response_model=User)
def get_user(
    session: DBSession,
    user_id: int
) -> DBUser:
    """Gets a user object"""
    return users_db.get_by_id(session, user_id)