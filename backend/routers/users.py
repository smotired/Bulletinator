"""Router for user routes.

Args:
    router (APIRouter): Router for /users routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend.dependencies import DBSession

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/", status_code=200)
def get_users(session: DBSession) -> dict:
    return {"message": "Getting users"}