"""Router for board item routes.

Args:
    router (APIRouter): Router for /boards/{board_id}/items routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend.dependencies import DBSession

router = APIRouter(prefix="/boards/{board_id}/items", tags=["Item"])

@router.get("/", status_code=200)
def get_users(session: DBSession, board_id: int) -> dict:
    return {"message": f"Getting items for board {board_id}"}