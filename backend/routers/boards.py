"""Router for boards routes.

Args:
    router (APIRouter): Router for /boards routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend.dependencies import DBSession

router = APIRouter(prefix="/boards", tags=["Board"])

@router.get("/", status_code=200)
def get_boards(session: DBSession) -> dict:
    return {"message": "Getting boards"}