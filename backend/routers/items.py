"""Router for board item routes.

Args:
    router (APIRouter): Router for /boards/{board_id}/items routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend.database import items as items_db
from backend.dependencies import DBSession, CurrentUser, OptionalUser
from backend.models.items import *
from backend.models.shared import Metadata

router = APIRouter(prefix="/boards/{board_id}/items", tags=["Item"])

@router.get("/", status_code=200)
def get_items(session: DBSession, board_id: int, user: OptionalUser) -> ItemCollection:
    """If the current user can see the board with this ID, return a collection of all items on this board."""
    items = convert_item_list( items_db.get_items(session, board_id, user) )
    return ItemCollection(
        metadata=Metadata(count=len(items)),
        items=items
    )