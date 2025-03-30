from sqlalchemy import select
from sqlalchemy.orm import selectin_polymorphic, selectinload

from backend.dependencies import DBSession
from backend.database import boards as boards_db
from backend.database.schema import DBItem, DBBoard, DBUser, DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList
from backend.exceptions import *

from backend.models.items import *

# options for select
polymorphic = selectin_polymorphic(DBItem, [DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList])
loadlistcontents = selectinload(DBItemList.contents).options(polymorphic)

def get_by_id(session: DBSession, item_id: int) -> DBItem:
    """Returns the item with this ID"""
    # tragically due to polymorphism session.get doesn't work
    stmt = select(DBItem).options(polymorphic, loadlistcontents).where(DBItem.id == item_id)
    results = list(session.execute(stmt).scalars().all())
    if len(results) == 0:
        raise EntityNotFound("item", "id", item_id)
    return results[0]

def get_items(session: DBSession, board_id: int, user: DBUser | None) -> list[DBItem]:
    """Returns the items on the board with this ID, if the user can see them"""
    board: DBBoard = boards_db.get_for_viewer(session, board_id, user)
    # Get a list of top-level items
    stmt = select(DBItem).options(polymorphic, loadlistcontents).where(DBItem.board_id == board_id).where(DBItem.list_id == None)
    items = list(session.execute(stmt).scalars().all())
    return items

def get_item(session: DBSession, board_id: int, item_id: int, user: DBUser | None) -> DBItem:
    """Returns the item with this ID, if it's on the board with this ID and the user can see it."""
    board: DBBoard = boards_db.get_for_viewer(session, board_id, user)
    item = get_by_id(session, item_id)
    if item.board != board:
        raise EntityNotFound("item", "id", item_id)
    return item
