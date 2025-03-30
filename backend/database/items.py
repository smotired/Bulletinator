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
    item: DBItem | None = session.get(DBItem, item_id)
    if item is None:
        raise EntityNotFound("item", "id", item_id)
    return item

def get_items(session: DBSession, board_id: int, user: DBUser | None) -> list[DBItem]:
    """Returns the items on the board with this ID, if the user can see them"""
    board: DBBoard = boards_db.get_by_id(session, board_id)
    if not boards_db.can_see(session, board, user):
        raise EntityNotFound("board", "id", board_id)
    # Get a list of top-level items
    stmt = select(DBItem).options(polymorphic, loadlistcontents).where(DBItem.board_id == board_id).where(DBItem.list_id == None)
    items = list(session.execute(stmt).scalars().all())
    return items