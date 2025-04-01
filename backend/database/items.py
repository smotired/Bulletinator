from random import random

from sqlalchemy import select
from sqlalchemy.orm import selectin_polymorphic, selectinload

from backend.dependencies import DBSession, format_list
from backend.database import boards as boards_db
from backend.database.schema import DBItem, DBBoard, DBUser, DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList, DBPin
from backend.exceptions import *

from backend.models.items import *

# options for select
polymorphic = selectin_polymorphic(DBItem, [DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList])
loadlistcontents = selectinload(DBItemList.contents).options(polymorphic)

def get_by_id(session: DBSession, item_id: int, typestr: str = 'item') -> DBItem:
    """Returns the item with this ID"""
    # tragically due to polymorphism session.get doesn't work
    stmt = select(DBItem).options(polymorphic, loadlistcontents).where(DBItem.id == item_id)
    results = list(session.execute(stmt).scalars().all())
    if len(results) == 0:
        raise EntityNotFound(typestr, "id", item_id)
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
    # If a list_id is provided, try to get the list from the database and make some space
    if config_dict['list_id'] is not None:
        # make sure we aren't adding a list to a list
        if config.type == 'list':
            raise AddListToList()
        other: DBItemList = get_by_id(session, config_dict['list_id'], 'item_list')
        # make sure the list is also on this board
        if other.board_id != board_id:
            raise EntityNotFound('item_list', 'id', config_dict['list_id'])
        # make sure the other item is a list
        if other.type != "list":
            raise ItemTypeMismatch(other.id, 'list', other.type)
        # try to make space
        target = config_dict['index'] or len(other.contents)
        other = shift_list(session, other, target) # THIS MODIFIES THE DATABASE! IF MORE ERROR HANDLING IS ADDED TO THIS METHOD, IT MUST BE BEFORE THIS LINE!
        config_dict['index'] = target
    # Create a minimal dictionary
    dbclass: type = ITEMTYPES.get(config.type)['db']
    stripped_dict = dict( (k, v) for k, v in config_dict.items() if k in ITEMFIELDS or v is not None ) # remove fields for different subclasses
    stripped_dict['board_id'] = board_id
    # Create a DBItem for the subclass and add it to the database
    item: DBItem = dbclass(**stripped_dict)
    # Make sure to override position and index based on list status
    if item.list_id is not None:
        item.position = None
    else:
        item.index = None
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def update_item(session: DBSession, board_id: int, item_id: int, config: ItemUpdate, user: DBUser) -> DBItem:
    """Updates an item."""
    # Make sure the user can edit this board, and the item exists and is on this board.
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    item: DBItem = get_by_id(session, item_id)
    if item.board_id != board_id:
        raise EntityNotFound('item', 'id', item_id)
    # Update subclass-specific item fields
    if config.text is not None and item.type in [ 'note' ]:
        item.text = config.text
    if config.size is not None and item.type in [ 'note', 'media' ]:
        item.size = config.size
    if config.title is not None and item.type in [ 'link', 'todo', 'list' ]:
        item.title = config.title
    if config.url is not None and item.type in [ 'link', 'media' ]:
        item.url = config.url
    # Only universal fields that can be updated are position, link and index.
    lists_to_collapse: list[DBItemList] = [] # lists that had things removed or swapped around and should be collapsed after items are updated
    # If a position is provided, remove from any list.
    if config.position is not None:
        if item.list:
            lists_to_collapse.append(item.list)
        item.list_id = None
        item.index = None
        item.position = config.position
    # ELSE, if a list_id is provided that doesn't match the current list_id, remove from the current list and add to that list.
    elif config.list_id is not None and config.list_id != item.list_id:
        # make sure we aren't adding a list to a list
        if item.type == 'list':
            raise AddListToList()
        # make sure we actually can add to the other list, if not, leave as-is
        other: DBItemList = get_by_id(session, config.list_id, 'item_list')
        # make sure the list is also on this board
        if other.board_id != board_id:
            raise EntityNotFound('item_list', 'id', config.list_id)
        # make sure the other item is a list
        if other.type != "list":
            raise ItemTypeMismatch(other.id, 'list', other.type)
        # try to make space
        target = config.index if config.index is not None else len(other.contents)
        other = shift_list(session, other, target) # THIS MODIFIES THE DATABASE! IF MORE ERROR HANDLING IS ADDED TO THIS METHOD, IT MUST BE BEFORE THIS LINE!
        config.index = target
        # prepare to move
        if item.list:
            lists_to_collapse.append(item.list)
        item.list_id = config.list_id
        item.index = config.index
        item.position = None
    # ELSE, if index is provided, update position in current list (list_id either isn't provided or is the same so that's fine. unless this isn't in a list in which case should throw indexoutofrange)
    elif config.index is not None:
        if item.list_id is None:
            raise IndexOutOfRange('item', item_id, config.index)
        # make space and prepare to move
        lists_to_collapse.append(item.list)
        item.list = shift_list(session, item.list, config.index)
        item.index = config.index
    # OTHERWISE nothing about the item's location was provided, so leave that alone.
    # Update in database.
    session.add(item)
    session.commit()
    session.refresh(item)
    # Collapse lists before returning
    for l in lists_to_collapse:
        collapse_list(session, l)
    return item

def delete_item(session: DBSession, board_id: int, item_id: int, user: DBUser) -> None:
    """Delets an item."""
    # Make sure the user can edit this board, and the item exists and is on this board.
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    item: DBItem = get_by_id(session, item_id)
    if item.board_id != board_id:
        raise EntityNotFound('item', 'id', item_id)
    # Deleting a list deletes all child objects with ondelete=cascade
    # Delete and collapse any containing list
    item_list: DBItemList | None = item.list
    session.delete(item)
    session.commit()
    if item_list:
        collapse_list(session, item_list)

def create_todo_item(session: DBSession, board_id: int, config: TodoItemCreate, user: DBUser) -> DBTodoItem:
    """Creates and returns a TodoItem in this todo list"""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    todo: DBItemTodo = get_by_id(session, config.list_id, 'item_todo')
    if todo.board_id != board_id:
        raise EntityNotFound('item_todo', 'id', config.list_id)
    if todo.type != 'todo':
        raise ItemTypeMismatch(todo.id, 'todo', todo.type)
    todo_item = DBTodoItem(
        list_id = config.list_id,
        text=config.text,
        link=config.link,
        done=config.done
    )
    session.add(todo_item)
    session.commit()
    session.refresh(todo_item)
    return todo_item

def update_todo_item(session: DBSession, board_id: int, todo_item_id: int, config: TodoItemUpdate, user: DBUser) -> DBTodoItem:
    """Creates and returns a TodoItem in this todo list"""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    todo_item = session.get(DBTodoItem, todo_item_id)
    if todo_item == None:
        raise EntityNotFound('todo_item', 'id', todo_item_id)
    todo: DBItemTodo = get_by_id(session, todo_item.list_id, 'item_todo')
    if todo.board_id != board_id:
        raise EntityNotFound(f'todo_item', 'id', todo_item_id)
    if todo.type != 'todo':
        raise ItemTypeMismatch(todo.id, 'todo', todo.type)
    # update fields
    todo_item.text = config.text or todo_item.text
    todo_item.link = config.link or todo_item.link
    todo_item.done = config.done or todo_item.done
    session.add(todo_item)
    session.commit()
    session.refresh(todo_item)
    return todo_item

def delete_todo_item(session: DBSession, board_id: int, todo_item_id: int, user: DBUser) -> None:
    """Deletes a todo item"""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    todo_item = session.get(DBTodoItem, todo_item_id)
    if todo_item == None:
        raise EntityNotFound('todo_item', 'id', todo_item_id)
    todo: DBItemTodo = get_by_id(session, todo_item.list_id, 'item_todo')
    if todo.board_id != board_id:
        raise EntityNotFound('todo_item', 'id', todo_item_id)
    if todo.type != 'todo':
        raise ItemTypeMismatch(todo.id, 'todo', todo.type)
    session.delete(todo_item)
    session.commit()

def shift_list(session: DBSession, list: DBItemList, start_index: int) -> DBItemList:
    """Shifts the items on this list after this index by one, leaving an open space, and then return the list. Used for when you want to add something at this new index."""
    if start_index < 0 or start_index > len(list.contents):
        raise IndexOutOfRange("item_list", list.id, start_index)
    sorted_contents = sorted(list.contents, key=lambda item: item.index)
    # update all the item indices
    for i, item in enumerate(sorted_contents):
        if i >= start_index:
            item.index = i + 1
            session.add(item)
    session.commit()
    session.refresh(list)
    return list

def collapse_list(session: DBSession, list: DBItemList) -> DBItemList:
    """Refreshes a list's indices. Replaces them so they start at 0 and go up by 1."""
    sorted_contents = sorted(list.contents, key=lambda item: item.index)
    # update all the item indices
    for i, item in enumerate(sorted_contents):
        item.index = i
        session.add(item)
    session.commit()
    session.refresh(list)
    return list

def create_pin(session: DBSession, board_id: int, config: PinCreate, user: DBUser) -> DBPin:
    """Adds a pin to an item."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    item: DBItem = get_by_id(session, config.item_id)
    if item.board_id != board_id:
        raise EntityNotFound('item', 'id', config.item_id)
    if item.pin is not None:
        raise DuplicateEntity('pin', 'item_id', config.item_id)
    pin = DBPin(
        board_id=board_id,
        item_id=config.item_id,
        label=config.label,
        compass=config.compass,
    )
    session.add(pin)
    session.commit()
    session.refresh(pin)
    return pin

def update_pin(session: DBSession, board_id: int, pin_id: int, config: PinUpdate, user: DBUser) -> DBPin:
    """Updates a pin."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    pin: DBPin = session.get(DBPin, pin_id)
    if pin == None:
        raise EntityNotFound('pin', 'id', pin_id)
    if config.item_id is not None:
        item: DBItem = get_by_id(session, config.item_id)
        if item.board_id != board_id:
            raise EntityNotFound('item', 'id', config.item_id)
        if item.pin is not None:
            raise DuplicateEntity('pin', 'item_id', config.item_id)
        pin.item_id = config.item_id
    pin.label = config.label if config.label is not None else pin.label
    pin.compass = config.compass if config.compass is not None else pin.compass
    session.add(pin)
    session.commit()
    session.refresh(pin)
    return pin

def delete_pin(session: DBSession, board_id: int, pin_id: int, user: DBUser) -> None:
    """Deletes a pin."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    pin: DBPin = session.get(DBPin, pin_id)
    if pin == None:
        raise EntityNotFound('pin', 'id', pin_id)
    session.delete(pin)
    session.commit()

def add_pin_connection(session: DBSession, board_id: int, pin1_id: int, pin2_id: int, user: DBUser) -> list[DBPin]:
    """Adds a connection between two pins."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    pin1: DBPin = session.get(DBPin, pin1_id)
    if pin1 == None:
        raise EntityNotFound('pin', 'id', pin1_id)
    pin2: DBPin = session.get(DBPin, pin2_id)
    if pin2 == None:
        raise EntityNotFound('pin', 'id', pin2_id)
    pin1.connections.append(pin2)
    pin2.connections.append(pin1)
    session.add(pin1)
    session.add(pin2)
    session.commit()
    session.refresh(pin1)
    session.refresh(pin2)
    return [ pin1, pin2 ]

def remove_pin_connection(session: DBSession, board_id: int, pin1_id: int, pin2_id: int, user: DBUser) -> list[DBPin]:
    """Removes a connection between two pins."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, user)
    pin1: DBPin = session.get(DBPin, pin1_id)
    if pin1 == None:
        raise EntityNotFound('pin', 'id', pin1_id)
    pin2: DBPin = session.get(DBPin, pin2_id)
    if pin2 == None:
        raise EntityNotFound('pin', 'id', pin2_id)
    pin1.connections.remove(pin2)
    pin2.connections.remove(pin1)
    session.add(pin1)
    session.add(pin2)
    session.commit()
    session.refresh(pin1)
    session.refresh(pin2)
    return [ pin1, pin2 ]
