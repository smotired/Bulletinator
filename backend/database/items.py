from sqlalchemy import select
from sqlalchemy.orm import selectin_polymorphic, selectinload

from backend.dependencies import DBSession, format_list
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

def create_item(session: DBSession, board_id: int, config: ItemCreate, user: DBUser | None) -> DBItem:
    """Creates an item on this board."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    # Figure out what type of config this is
    subclass: type = ITEMTYPES.get(config.type, { "create": BaseItemCreate })['create']
    if subclass == BaseItemCreate:
        raise InvalidItemType(config.type)
    # Make sure it has the required fields
    config_dict = config.model_dump()
    required_fields: list[str] = ITEMTYPES.get(config.type)['required_fields'] # does not include Item's required fields, as those are required in BaseItemUpdate
    missing = [ f for f in required_fields if config_dict[f] == None ]
    if len(missing) > 0:
        raise MissingItemFields(config.type, format_list(missing))
    # Create a DBItem for the subclass and add it to the database
    dbclass: type = ITEMTYPES.get(config.type)['db']
    stripped_dict = dict( (k, v) for k, v in config_dict.items() if k in ITEMFIELDS or v is not None ) # remove optional/not provided options
    stripped_dict['board_id'] = board_id
    item = dbclass(**stripped_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item